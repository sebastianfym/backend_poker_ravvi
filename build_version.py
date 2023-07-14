#!/usr/bin/python3

import os
import subprocess
import packaging.version
import re

build_dir = os.path.dirname(os.path.abspath(__file__))

def _exec(cmd):
    try:
        stdout = subprocess.check_output(cmd, shell=True, text=True, cwd=build_dir)
    except subprocess.CalledProcessError as e:
        stdout = e.output
    lines = stdout.splitlines()
    return lines

def git_version_tags():
    return _exec("git tag --list 'v*'")

def git_tagged_versions():
    tags = git_version_tags()
    result = []
    for tag in tags:
        try:
            v = packaging.version.parse(tag[1:])
            result.append(v)   
        except Exception as ex:
           pass
    result.sort(reverse=True)
    return result
                 
def git_branch():
    branch = _exec('git rev-parse --abbrev-ref HEAD')
    if isinstance(branch, list) and len(branch)==1:
        branch = branch[0]
    else:
        branch = None
    return branch

def get_version(branch, tag=None, build_id=1):
    print(branch, tag, build_id)
    if tag and tag[0]=="v":
        try:
            return packaging.version.parse(tag[1:])
        except:
            pass
    versions = git_tagged_versions()
    rb = re.findall("^release/v(\d+\.\d+)$", branch)
    if rb:
        rb = packaging.version.parse(rb[0]) if rb else None
        versions = [v for v in versions if (v.major,v.minor)==(rb.major,rb.minor)]
        if not versions:
            return packaging.version.parse(f"{rb.major}.{rb.minor}.{0}rc{0}.dev{build_id}")
        v = max(versions[0], rb)
        v = packaging.version.parse(f"{v.major}.{v.minor}.{v.micro+1}rc{0}.dev{build_id}")
        return v
    if versions:
        v = versions[0]
    else:
        tag = None
        v = packaging.version.parse("0.0.0")
    if branch=='master':
        post = v.post if v.is_postrelease else 0
        v = packaging.version.parse(f"{v.major}.{v.minor}.{v.micro}post{post+1}.dev{build_id}")
    elif branch=='develop':
        v = packaging.version.parse(f"{v.major}.{v.minor+1}.{0}b{0}.dev{build_id}")
    else:
        v = packaging.version.parse(f"{v.major}.{v.minor+1}.{0}a{0}.dev{build_id}")
    return v

def get_variables():
    if os.getenv("CI"):
        branch = os.getenv("CI_COMMIT_BRANCH")
        tag = os.getenv("CI_COMMIT_TAG")
        build_id = os.getenv("CI_PIPELINE_ID")
    else:
        branch = git_branch()
        tag = None
        build_id = 0
    version = get_version(branch, tag, build_id)
    VERSION_BUILD = str(version)
    s = ""
    if version.pre is not None:
        s = f"{version.pre[0]}{version.pre[1]}"
        if version.dev is not None:
            s+=f".dev{version.dev}"
    VERSION_BUILD_TUPLE = tuple(list(version.release)+[s])

    return dict(
        VERSION_BUILD=str(version),
        VERSION_BUILD_TUPLE=str(VERSION_BUILD_TUPLE)
    )

def replace_valiables(data, variables):
    for k, v in variables.items():
        print(k, v)
        data = data.replace("${"+k+"}",v)
    return data

if __name__=="__main__":
    variables = get_variables()

    template = os.path.join(build_dir,'ravvi_poker/build.py.template')
    result = template[:-9]
    with open(template,"r") as f:
        data = f.read()
    data = replace_valiables(data, variables)
    with open(result,"w") as f:
        f.write(data)
    