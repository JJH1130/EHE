"""Pure-python TIFF-flavor LZW decoder (early-change variant)."""

def lzw_decode(data: bytes) -> bytes:
    CLEAR = 256
    EOI = 257
    out = bytearray()

    def reset_table():
        table = [bytes([i]) for i in range(256)] + [b'', b'']
        return table

    table = reset_table()
    bitbuf = 0
    bitcnt = 0
    pos = 0
    codelen = 9
    prev = None

    n = len(data)

    def next_code():
        nonlocal bitbuf, bitcnt, pos
        while bitcnt < codelen:
            if pos >= n:
                return None
            bitbuf = (bitbuf << 8) | data[pos]
            pos += 1
            bitcnt += 8
        bitcnt -= codelen
        code = (bitbuf >> bitcnt) & ((1 << codelen) - 1)
        return code

    while True:
        code = next_code()
        if code is None or code == EOI:
            break
        if code == CLEAR:
            table = reset_table()
            codelen = 9
            prev = None
            continue
        if prev is None:
            entry = table[code]
            out += entry
            prev = entry
        else:
            if code < len(table):
                entry = table[code]
            elif code == len(table):
                entry = prev + prev[:1]
            else:
                raise ValueError(f"bad LZW code {code} table size {len(table)}")
            out += entry
            table.append(prev + entry[:1])
            prev = entry
        # early change: bump codelen one code early
        L = len(table)
        if L >= 511 and L < 1024 and codelen == 9:
            codelen = 10
        elif L >= 1023 and L < 2048 and codelen == 10:
            codelen = 11
        elif L >= 2047 and codelen == 11:
            codelen = 12
    return bytes(out)
