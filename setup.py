#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os, subprocess

def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pardus-font-manager.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-font-manager.mo"]))
    return mo

def compile_c_code():
    compile_cmd = "gcc src/font_adder.c -o libfontadder.so -shared -lfontconfig"
    if subprocess.call(compile_cmd, shell=True) != 0:
        raise RuntimeError("C code compilation failed!")
    return [("/usr/share/pardus/pardus-font-manager/src", ["libfontadder.so"])]

changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = "0.0.0"
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
    ("/usr/bin", ["pardus-font-manager"]),
    ("/usr/share/applications",
     ["data/tr.org.pardus.font-manager.desktop"]),
    ("/usr/share/pardus/pardus-font-manager/ui",
     ["ui/MainWindow.glade"]),
    ("/usr/share/pardus/pardus-font-manager/src",
     ["src/Main.py",
      "src/MainWindow.py",
      "src/add_font.py",
      "src/delete_font.py",
      "src/font_charmaps.py",
      "src/font_viewer.py",
      "src/__version__"]),
    ("/usr/share/icons/hicolor/scalable/apps/",
     ["data/pardus-font-manager.svg"])
] + create_mo_files() + compile_c_code()

setup(
    name="pardus-font-manager",
    version=version,
    packages=find_packages(),
    scripts=["pardus-font-manager"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Emel Öztürk",
    author_email="emel.ozturk@pardus.org.tr",
    description="Simple Font Manager",
    license="GPLv3",
    keywords="pardus-font-manager, font, otf, ttf",
    url="https://github.com/pardus/pardus-font-manager",
)
