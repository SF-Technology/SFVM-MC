#coding=utf-8
__author__ =  ""
'''
 加密和解密模块
 KEY必须是16字节或24字节"

    用法:
        加密:
              print encrypt('123456')
              输出  wBeB+BZ0ABg=

        解密:
              print decrypt("wBeB+BZ0ABg=")
              输出 123456

         encrypt和decrypt中的key参数可以自行更换,但是必须是16个字节或24个字节
'''

from pyDes import *
from base64 import *
import sys


def encrypt(str, key="ABCD-DBACFFF-KEY"):
    k = triple_des(key, CBC, "\0\1\2\3\4\5\6\7", pad=None, padmode=PAD_PKCS5)
    return encodestring(k.encrypt(str))[:-1]


def decrypt(str, key="ABCD-DBACFFF-KEY"):
    k = triple_des(key, CBC, "\0\1\2\3\4\5\6\7", pad=None, padmode=PAD_PKCS5)
    return k.decrypt(decodestring(str))


def encrypt_str_aes(text, key='1234567812345678', iv='Pkcs7'):
    '''
        AES加密
    :param text:
    :param key: the length can be (16, 24, 32)
    :param iv:
    :return:
    '''
    try:
        from Crypto.Cipher import AES
    except:
        return text
    import base64

    BS = AES.block_size
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
    unpad = lambda s: s[0:-ord(s[-1])]

    cipher = AES.new(key, IV=iv)

    encrypted = cipher.encrypt(pad(text))
    # print encrypted  # will be something like 'f456a6b0e54e35f2711a9fa078a76d16'
    result = base64.b64encode(encrypted)
    return result  # will be something like 'f456a6b0e54e35f2711a9fa078a76d16'


def decrypt_str_aes(encryptstr, key='1234567812345678', iv='Pkcs7'):
    '''
        AES解密
    :param encryptstr:
    :param key:
    :param iv:
    :return:
    '''
    try:
        from Crypto.Cipher import AES
    except:
        return encryptstr
        pass
    import base64
    unpad = lambda s: s[0:-ord(s[-1])]

    cipher = AES.new(key, IV=iv)
    result2 = base64.b64decode(encryptstr)
    decrypted = unpad(cipher.decrypt(result2))
    return decrypted  # will be 'to be encrypted'

if __name__ == '__main__':
    # if len(sys.argv) == 3:
    #     if sys.argv[1] == '-E':
    #         print encrypt(sys.argv[2])
    #     elif sys.argv[1] == '-D':
    #         print decrypt(sys.argv[2])
    # elif len(sys.argv) == 4:
    #     if sys.argv[1] == '-E':
    #         print encrypt(sys.argv[2], sys.argv[3])
    #     elif sys.argv[1] == '-D':
    #         print decrypt(sys.argv[2], sys.argv[3])

    # print encrypt('passwd123')

    # print encrypt_str_aes('passwd123')

    print decrypt('4Z4lY6M/Hl4Bx105SR0aTw==')
    print decrypt('y2arnvLYRzNlNxLKkwk7HQ==')