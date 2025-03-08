from opencc import OpenCC

def t2c(text):
    cc = OpenCC('t2s')
    return cc.convert(text)