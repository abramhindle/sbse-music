import json
import re
import random
import copy
import argparse

example = {
    "type":"ugen",
    "class":"BPF",
    "parameters":[
        {"type":"parameter", "name":"in","value":{"type":"ugen","class":"SinOsc","parameters":[{"type":"parameter","name":"frequency","value":{"type":"float","value":440}}]}},
        {"type":"parameter", "name":"frequency","value":{"type":"integer","value":440}},
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
        return args.get(param_name,"XXXXMISSINGXXX")
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

choose = random.choice

def generate_frequency(param=None):
    if param is None:
        return {"type":"float","value":random.uniform(20,10000.0)}
    else:
        mini = param.get("min",20)
        maxi = param.get("max",12000)
        return {"type":"float","value":random.uniform(mini,maxi)}


def generate_float(param=None):
    if param is None:
        return {"type":"float","value":random.uniform(0,22000.0)}
    else:
        mini = param.get("min",0)
        maxi = param.get("max",1.0)
        return {"type":"float","value":random.uniform(mini,maxi)}

def generate_integer(param=None):
    if param is None:
        return {"type":"integer","value":random.randint(0,22000)}
    else:
        mini = int(param.get("min",0))
        maxi = int(param.get("max",22000))
        return {"type":"integer","value":random.randint(mini,maxi)}

def generate_ugen(param=None):
    my_ugen_name = choose(ugen_list)
    my_ugen_def  = ugens[my_ugen_name]
    new_ugen = copy.deepcopy(my_ugen_def)
    params = [ fill_parameter(new_ugen,p["name"]) for p in new_ugen["parameters"] ]
    new_ugen["parameters"] = params
    return new_ugen


def generate_param(param_type,param=None):
    if param_type == "float":
        return generate_float(param=param)
    if param_type == "frequency":
        return generate_frequency(param=param)
    if param_type == "integer":
        return generate_integer(param=param)
    if param_type == "ugen":
        return generate_ugen(param=param)

def replace_parameter(ugen, param_name, new_param):
    """ mutates the ugen! """
    new_ugen = copy.deepcopy(ugen)
    for i in range(0,len(ugen["parameters"])):
        if ugen["parameters"][i]["name"] == param_name:
            new_ugen["parameters"][i] = new_param
    return new_ugen
    
def fill_parameter(ugen,param_name,param_type=None):
    assert ugen["type"] == "ugen"
    new_ugen = copy.deepcopy(ugen)
    definition = ugens[ugen["class"]]
    param = [p for p in definition["parameters"] if p["name"] == param_name][0]
    new_param = copy.deepcopy(param)
    if param_type is None:
        hole_type = choose(new_param["values"])
    else:
        hole_type = param_type
    del(new_param["values"])
    new_param["value"] = generate_param(hole_type,param=new_param)
    return new_param
    
    

def test_fill_parameter():
    ugen_s = {"type":"ugen","class":"SinOsc","parameters":[{"type":"parameter","name":"frequency"}]}
    new_ugen_s = replace_parameter(ugen_s, "frequency", fill_parameter(ugen_s,"frequency"))
    assert "parameters" in new_ugen_s, "missing parameters %s" % str(new_ugen_s)
    assert new_ugen_s["parameters"][0]["name"] == "frequency", "it's still frequency"
    assert new_ugen_s["parameters"][0].get("value",None) is not None, "has Value"
    assert new_ugen_s["parameters"][0]["value"].get("type",None) is not None, "has Type"
    print(str(new_ugen_s))

def tests():
    test_templater()
    test_gen_param_dict()
    test_render()
    test_fill_parameter()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate some SuperCollider Code')
    parser.add_argument('--test', action='store_true',help="run tests")
    args = parser.parse_args()
    if args.test:
        tests()
    else:
        print render(generate_ugen())
