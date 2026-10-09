import struct
import numpy as np

def read_shp_points(path):
    with open(path, 'rb') as f:
        data = f.read()
    # header: 100 bytes. shape type at offset 32 (should be 1 = Point)
    shape_type = struct.unpack('<i', data[32:36])[0]
    assert shape_type == 1, f"expected Point (1), got {shape_type}"
    pos = 100
    n = len(data)
    xs, ys = [], []
    while pos < n:
        rec_num, content_len = struct.unpack('>ii', data[pos:pos+8])
        pos += 8
        rec_shape_type = struct.unpack('<i', data[pos:pos+4])[0]
        assert rec_shape_type == 1
        x, y = struct.unpack('<dd', data[pos+4:pos+20])
        xs.append(x); ys.append(y)
        pos += content_len * 2  # content_len is in 16-bit words
    return np.array(xs), np.array(ys)


def read_dbf(path):
    with open(path, 'rb') as f:
        header = f.read(32)
        num_records = struct.unpack('<I', header[4:8])[0]
        header_len = struct.unpack('<H', header[8:10])[0]
        record_len = struct.unpack('<H', header[10:12])[0]
        fields = []
        f.seek(32)
        while True:
            fd = f.read(32)
            if fd[0:1] == b'\r':
                break
            name = fd[0:11].split(b'\x00')[0].decode('latin1')
            ftype = fd[11:12].decode('latin1')
            flen = fd[16]
            fdec = fd[17]
            fields.append((name, ftype, flen, fdec))
        # data starts after header_len bytes total (terminator already consumed)
        f.seek(header_len)
        records = []
        for i in range(num_records):
            rec = f.read(record_len)
            if len(rec) < record_len:
                break
            deleted = rec[0:1]
            row = {}
            off = 1
            for (name, ftype, flen, fdec) in fields:
                raw = rec[off:off+flen]
                off += flen
                s = raw.decode('utf-8', errors='replace').strip()
                if ftype in ('N', 'F'):
                    try:
                        val = float(s) if s not in ('', '.') else None
                    except ValueError:
                        val = None
                else:
                    val = s
                row[name] = val
            records.append(row)
    return fields, records


if __name__ == "__main__":
    import time
    t0 = time.time()
    xs, ys = read_shp_points("point_data.shp")
    print("points:", len(xs), "time:", time.time()-t0)
    print("x range:", xs.min(), xs.max())
    print("y range:", ys.min(), ys.max())

    t0 = time.time()
    fields, records = read_dbf("point_data.dbf")
    print("dbf records:", len(records), "time:", time.time()-t0)
    print(fields)
    print(records[0])
    print(records[1])
    assert len(records) == len(xs), f"mismatch: {len(records)} vs {len(xs)}"
    print("OK: shp and dbf record counts match")
