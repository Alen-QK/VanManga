from opencc import OpenCC

def t2c(text):
    cc = OpenCC('t2c')
    return cc.convert(text)