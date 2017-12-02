import json
import re

example = {
    "type":"ugen",
    "class":"BPF",
    "parameters":[
        {"type":"parameter", "name":"in","value":{"type":"ugen","class":"SinOsc","parameters":[{"type":"parameter","name":"frequency","value":{"type":"float","value":440}}]}},
        {"type":"parameter", "name":"center","value":{"type":"integer","value":440}},
        {"type":"parameter", "name":"q", "value":{"type":"float","value":0.75}},
    ]
}



ugen_list = ["BPF","LPF","SinOsc","add"]

def load_type(prefix, suffix):
    return json.load(file("types/%s-%s.json" % (prefix,suffix)))

def load_template(prefix, suffix):
    return file("templates/%s-%s.txt" % (prefix,suffix)).read()

def load_base():
    return file("templates/base.txt").read()

ugens = {name:load_type("ugen",name) for name in ugen_list}
ugen_templates = {name:load_template("ugen",name) for name in ugen_list }

def templater(template,args):
    def replacer(matchobj):
        param_name = matchobj.group(0)[2:-1]
        return args[param_name]
    res = re.sub( r'\$\{([^}]+)\}', replacer, template )
    return res

def test_templater():
    template = "${1} ${first} ${second} ${2} ${b}"
    first = "what"
    second = "huh"
    b = "zuh"
    one = first
    two = second
    compare_str = "%s %s %s %s %s" % (one, first, second, two, b)
    output = templater(template,{"1":one,"2":two,"first":first,"second":second,"b":b})
    assert output == compare_str, ("Templater doesn't match [%s][%s]" % (compare_str,output))

def gen_param_dict(params):
    out = {}
    counter = 1
    for param in params:
        out[param["name"]] = param["rendered"]
        out[str(counter)]  = param["rendered"]
        counter += 1
    return out

def test_gen_param_dict():
    sinosc = "SinOsc.ar(440)"
    parameters = [
        {"type":"parameter", "name":"in","rendered":sinosc},
        {"type":"parameter", "name":"center","rendered":"440.0"},
        {"type":"parameter", "name":"q", "rendered":"0.75"}
    ]
    out = gen_param_dict(parameters)
    assert out["center"] == "440.0", "center"
    assert out["2"] == "440.0", "center"
    assert out["1"] == sinosc, "SinOsc"

def render_ugen(concrete):
    template = ugen_templates[concrete["class"]]
    parameters = concrete["parameters"]
    for param in concrete["parameters"]:
        param["rendered"] = render(param)
    param_dict = gen_param_dict(parameters)
    return templater(template,param_dict)

def render(concrete):
    if concrete["type"] == "float":
        return str(concrete["value"])
    if concrete["type"] == "integer":
        return str(concrete["value"])
    if concrete["type"] == "parameter":
        return render(concrete["value"])
    if concrete["type"] == "ugen":
        return render_ugen(concrete)
    raise Exception("Can't render: %s" % str(concrete))

def test_render():
    ugen_s = {"type":"ugen","class":"SinOsc", "parameters":[{"type":"parameter","name":"frequency","value":{"type":"float","value":440}}]}
    assert render({"type":"float","value":440}) == "440", "Floats"
    assert render({"type":"float","value":440.1}) == "440.1", "Floats"
    assert render({"type":"integer","value":220}) == "220", "Integers"
    ugen_rendering = render(ugen_s)
    assert ugen_rendering.strip()  == "SinOsc.ar( freq:( 440 ))", "SinOsc [%s]" % ugen_rendering
    print render(example)

    
if __name__ == "__main__":
    test_templater()
    test_gen_param_dict()
    test_render()
