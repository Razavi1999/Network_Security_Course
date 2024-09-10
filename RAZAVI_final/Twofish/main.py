import struct
import string
# GF modulus polynomial for MDS matrix
GF_MOD = 2**8 + 2**6 + 2**5 + 2**3 + 1

# GF modulus polynomial for RS code
RS_MOD = 2**8 + 2**6 + 2**3 + 2**2 + 1

ROUNDS = 16

def to32Char(X):
    return list(struct.unpack('>BBBB', struct.pack('>I', X)))

def bytesTo32Bits(l):
    t = 0
    for i in l:
        t = t << 8
        t = t + i
    return t

def ROR(x, n):
    # assumes 32 bit words
    mask = (2**n) - 1
    mask_bits = x & mask
    return (x >> n) | (mask_bits << (32 - n))

def ROL(x, n):
    return ROR(x, 32 - n)

def ROR4(x, n): # rotate 4 bit value
    mask = (2**n) - 1
    mask_bits = x & mask
    return (x >> n) | (mask_bits << (4 - n))

def polyMult(a, b):
    t = 0
    while a:
        if a & 1:
            t = t ^ b
        b = b << 1
        a = a >> 1
    return t

def gfMod(t, modulus):
    modulus = modulus << 7
    for _ in range(8):
        tt = t ^ modulus
        if tt < t:
            t = tt
        modulus = modulus >> 1
    return t

def gfMult(a, b, modulus):
    return gfMod(polyMult(a, b), modulus)

def matrixMultiply(md, sd, modulus):
    r = []
    for j in range(len(md)):
        t = 0
        for k in range(len(sd)):
            t = t ^ gfMult(md[j][k], sd[k], modulus)
        r.insert(0, t)
    return r

MDS = [
    [ 0x01, 0xEF, 0x5B, 0x5B ],
    [ 0x5B, 0xEF, 0xEF, 0x01 ],
    [ 0xEF, 0x5B, 0x01, 0xEF ],
    [ 0xEF, 0x01, 0xEF, 0x5B ],
]

RS = [
    [ 0x01, 0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E ],
    [ 0xA4, 0x56, 0x82, 0xF3, 0x1E, 0xC6, 0x68, 0xE5 ],
    [ 0x02, 0xA1, 0xFC, 0xC1, 0x47, 0xAE, 0x3D, 0x19 ],
    [ 0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E, 0x03 ],
]

Q0 = [
    [ 0x8,0x1,0x7,0xD, 0x6,0xF,0x3,0x2, 0x0,0xB,0x5,0x9, 0xE,0xC,0xA,0x4 ],
    [ 0xE,0xC,0xB,0x8, 0x1,0x2,0x3,0x5, 0xF,0x4,0xA,0x6, 0x7,0x0,0x9,0xD ],
    [ 0xB,0xA,0x5,0xE, 0x6,0xD,0x9,0x0, 0xC,0x8,0xF,0x3, 0x2,0x4,0x7,0x1 ],
    [ 0xD,0x7,0xF,0x4, 0x1,0x2,0x6,0xE, 0x9,0xB,0x3,0x0, 0x8,0x5,0xC,0xA ],
]

Q1 = [
    [ 0x2,0x8,0xB,0xD, 0xF,0x7,0x6,0xE, 0x3,0x1,0x9,0x4, 0x0,0xA,0xC,0x5 ],
    [ 0x1,0xE,0x2,0xB, 0x4,0xC,0x3,0x7, 0x6,0xD,0xA,0x5, 0xF,0x9,0x0,0x8 ],
    [ 0x4,0xC,0x7,0x5, 0x1,0x6,0x9,0xA, 0x0,0xE,0xD,0x8, 0x2,0xB,0x3,0xF ],
    [ 0xB,0x9,0x5,0x1, 0xC,0x3,0xD,0xE, 0x6,0x4,0x7,0xF, 0x2,0x0,0x8,0xA ],
]

def printRoundKeys(K):
    for i in range(0, len(K), 2):
        print('%8s %8s' % (hex(K[i])[2:], hex(K[i+1])[2:]))

def keySched(M, N): #M is key text in 32 bit words, N is bit width of M
    k = (N + 63) // 64

    Me = [M[x] for x in range(0, (2 * k - 1), 2)]
    Mo = [M[x] for x in range(1, (2 * k), 2)]

    S = []
    for i in range(0, k):
        x1 = to32Char(Me[i])
        x2 = to32Char(Mo[i])
        vector = x1 + x2
        prod = matrixMultiply(RS, vector, RS_MOD)
        prod.reverse()
        S.insert(0, bytesTo32Bits(prod))

    K = makeKey(Me, Mo, k)

    return K, k, S


def makeKey(Me, Mo, k):
    K = []
    rho = 0x01010101
    for i in range(ROUNDS + 4):
        A = h(2 * i * rho, Me, k)
        B = h((2 * i + 1) * rho, Mo, k)
        B = ROL(B, 8)
        K.append((A + B) & 0xFFFFFFFF)
        K.append(ROL((A + 2 * B) & 0xFFFFFFFF, 9))
    return K

def Qpermute(x, Q):
    a0, b0 = x // 16, x % 16
    a1 = a0 ^ b0
    b1 = (a0 ^ ROR4(b0, 1) ^ (8 * a0)) % 16
    a2, b2 = Q[0][a1], Q[1][b1]
    a3 = a2 ^ b2
    b3 = (a2 ^ ROR4(b2, 1) ^ (8 * a2)) % 16
    a4, b4 = Q[2][a3], Q[3][b3]

    return (16 * b4) + a4


def h(X, L, k):
    x = to32Char(X)
    x.reverse()
    l = [to32Char(L[i]) for i in range(k)]
    y = x[:]

    Qdones = [
        [Q1, Q0, Q1, Q0],
        [Q0, Q0, Q1, Q1],
        [Q0, Q1, Q0, Q1],
        [Q1, Q1, Q0, Q0],
        [Q1, Q0, Q0, Q1],
    ]

    for i in range(k-1, -1, -1):
        for j in range(4):
            y[j] = Qpermute(y[j], Qdones[i+1][j]) ^ l[i][j]

    for j in range(4):
        y[j] = Qpermute(y[j], Qdones[0][j])

    z = matrixMultiply(MDS, y, GF_MOD)
    return bytesTo32Bits(z)

def g(X, S, k):
    return h(X, S, k)

def F(R0, R1, r, K, k, S):
    T0 = g(R0, S, k)
    T1 = g(ROL(R1, 8), S, k)
    F0 = (T0 + T1 + K[2 * r + 8]) & 0xFFFFFFFF
    F1 = (T0 + 2 * T1 + K[2 * r + 9]) & 0xFFFFFFFF
    return F0, F1

def encrypt(K, k, S, PT):
    PT = [struct.unpack('>I', struct.pack('<I', x))[0] for x in PT]
    R = [PT[i] ^ K[i] for i in range(4)]

    for r in range(ROUNDS):
        NR = [0, 0, 0, 0]
        FR0, FR1 = F(R[0], R[1], r, K, k, S)
        NR[2] = ROR(R[2] ^ FR0, 1)
        NR[3] = ROL(R[3], 1) ^ FR1
        NR[0] = R[0]
        NR[1] = R[1]
        R = NR
        if r < ROUNDS - 1:
            R[0], R[2] = R[2], R[0]
            R[1], R[3] = R[3], R[1]

    R = [R[2], R[3], R[0], R[1]]
    R = [R[(i+2) % 4] ^ K[i+4] for i in range(4)]
    R = [struct.unpack('>I', struct.pack('<I', x))[0] for x in R]
    return R

def decrypt(K, k, S, PT):
    PT = [struct.unpack('>I', struct.pack('<I', x))[0] for x in PT]
    R = [PT[i] ^ K[i+4] for i in range(4)]

    for r in range(ROUNDS-1, -1, -1):
        NR = [0, 0, 0, 0]
        FR0, FR1 = F(R[0], R[1], r, K, k, S)
        NR[2] = ROL(R[2], 1) ^ FR0
        NR[3] = ROR(R[3] ^ FR1, 1)
        NR[0] = R[0]
        NR[1] = R[1]
        R = NR
        if r > 0:
            R[0], R[2] = R[2], R[0]
            R[1], R[3] = R[3], R[1]

    R = [R[2], R[3], R[0], R[1]]
    R = [R[(i+2) % 4] ^ K[i] for i in range(4)]
    R = [struct.unpack('>I', struct.pack('<I', x))[0] for x in R]
    return R

def testKey(K, k, S):
    print('subkeys')
    printRoundKeys(K)
    ct = encrypt(K, k, S, [0, 0, 0, 0])
    print('CT=', [hex(x) for x in ct])
    pt = decrypt(K, k, S, ct)
    print('PT=', [hex(x) for x in pt])
    print()

def dispLongList(v):
    return ''.join([str.zfill(hex(x)[2:], 8) for x in v])

def Itest128():
    ct = [0, 0, 0, 0]
    k = [0, 0, 0, 0]

    for i in range(49):
        K, Kk, KS = keySched(k, 128)
        nct = encrypt(K, Kk, KS, ct)
        print()
        print('I=%d' % (i+1))
        print('KEY=%s' % dispLongList(k))
        print('PT=%s' % dispLongList(ct))
        print('CT=%s' % dispLongList(nct))
        PT = decrypt(K, Kk, KS, nct)
        print(f'after decryption :PT={dispLongList(PT)}')
        k = ct
        ct = nct


def Itest256():
    ct = [0, 0, 0, 0]
    k1 = [0, 0, 0, 0]
    k2 = [0, 0, 0, 0]

    for i in range(16):
        K, Kk, KS = keySched(k1 + k2, 256)
        nct = encrypt(K, Kk, KS, ct)
        print()
        print(f'I={i + 1}')
        print(f'KEY={dispLongList(k1) + dispLongList(k2)}')
        print(f'PT={dispLongList(ct)}')
        print(f'CT={dispLongList(nct)}')
        PT = decrypt(K, Kk, KS, nct)
        print(f'after decryption :PT={dispLongList(PT)}')
        k2 = k1
        k1 = ct
        ct = nct


def Itest192():
    ct = [0, 0, 0, 0]
    k1 = [0, 0, 0, 0]
    k2 = [0, 0, 0, 0]

    for i in range(16):
        K, Kk, KS = keySched(k1 + k2, 192)
        nct = encrypt(K, Kk, KS, ct)
        print()
        print(f'I={i + 1}')
        print(f'KEY={dispLongList(k1) + dispLongList(k2[:2])}')
        print(f'PT={dispLongList(ct)}')
        print(f'CT={dispLongList(nct)}')
        PT = decrypt(K, Kk, KS, nct)
        print(f'after decryption :PT={dispLongList(PT)}')

        k2 = k1
        k1 = ct
        ct = nct


def bench():
    import time
    ENCS = 50
    k = [0, 0, 0, 0]
    pt = [0, 0, 0, 0]
    K, Kk, KS = keySched(k, 128)
    a = range(ENCS)
    b = time.time()
    for i in a:
        encrypt(K, Kk, KS, pt)
    e = time.time()
    print(f'time for {ENCS} encryptions: {e - b}')
    print('e/s:', (ENCS / (e - b)))
    print('b/s:', (16 * (ENCS / (e - b))))

    b = time.time()
    for i in a:
        keySched(k, 128)
    e = time.time()
    print(f'time for {ENCS} key setups: {e - b}')
    print('ks/s:', (ENCS / (e - b)))


if __name__ == '__main__':
    Itest256()
    # print hex(polyMult(0x5b, 3))
    # Itest192()
    # Itest256()

    # K, k, S = keySched([0, 0, 0, 0], 128)
    # testKey(K, k, S)
    # K, k, S = keySched([0x01234567, 0x89abcdef, 0xfedcba98, 0x76543210,
    #                    0x00112233, 0x44556677], 192)
    # testKey(K, k, S)

    # K, k, S = keySched([0x01234567, 0x89abcdef, 0xfedcba98, 0x76543210,
    #                    0x00112233, 0x44556677, 0x8899aabb, 0xccddeeff],
    #                   256)
    # testKey(K, k, S)

    # K, k, S = keySched([0xefcdab89, 0x67452301,
    #                    0x10325476, 0x98badcfe,
    #                    0x77665544, 0x33221100], 192)
    # PT= [0xDEADBEEF, 0xCAFEBABE, 0x86753090, 0x04554013]
    # CT = encrypt(K, k, S, PT)
    # print(dispLongList(CT))
    # PT = decrypt(K, k, S, CT)
    # print(dispLongList(PT))
    # bench()
    K, k, S = keySched([0x9F589F5C, 0xF6122C32, 0xB6BFEC2F, 0x2AE8C35A], 128)
    CT = encrypt(K, k, S,
                 [0xD491DB16, 0xE7B1C39E, 0x86CB086B, 0x789F5419])
    PT = decrypt(K,k,S,CT)
    print("-----------------------------------------")
    print(dispLongList(CT))
    print(dispLongList(PT))
