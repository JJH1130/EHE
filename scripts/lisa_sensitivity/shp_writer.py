"""Minimal pure-Python ESRI Shapefile writer (Point shapefiles only)."""
import struct
import datetime


def _pack_header(shape_type, n_bytes_total, xmin, ymin, xmax, ymax):
    file_len_words = n_bytes_total // 2
    header = struct.pack(">i", 9994)
    header += b"\x00" * 20  # 5 unused int32
    header += struct.pack(">i", file_len_words)
    header += struct.pack("<i", 1000)
    header += struct.pack("<i", shape_type)
    header += struct.pack("<dddd", xmin, ymin, xmax, ymax)
    header += struct.pack("<dddd", 0.0, 0.0, 0.0, 0.0)  # Z/M ranges
    assert len(header) == 100
    return header


def write_point_shp_shx(path_base, xs, ys):
    n = len(xs)
    xmin, xmax = float(min(xs)), float(max(xs))
    ymin, ymax = float(min(ys)), float(max(ys))

    rec_content_len_words = 10  # shapeType(4)+X(8)+Y(8) = 20 bytes = 10 words
    rec_total_bytes = 8 + 20  # record header + content
    shp_total_bytes = 100 + n * rec_total_bytes
    shx_total_bytes = 100 + n * 8

    shp = bytearray(_pack_header(1, shp_total_bytes, xmin, ymin, xmax, ymax))
    shx = bytearray(_pack_header(1, shx_total_bytes, xmin, ymin, xmax, ymax))

    offset_words = 50  # 100 bytes / 2
    for i in range(n):
        rec_num = i + 1
        shp += struct.pack(">ii", rec_num, rec_content_len_words)
        shp += struct.pack("<i", 1)
        shp += struct.pack("<dd", float(xs[i]), float(ys[i]))
        shx += struct.pack(">ii", offset_words, rec_content_len_words)
        offset_words += 4 + rec_content_len_words  # 8-byte header = 4 words

    with open(path_base + ".shp", "wb") as f:
        f.write(shp)
    with open(path_base + ".shx", "wb") as f:
        f.write(shx)


def write_dbf(path_base, fields, rows):
    """
    fields: list of (name, type, length, decimals)  type in {'C','N'}
    rows: list of tuples, same order as fields
    """
    n = len(rows)
    today = datetime.date.today()
    header = bytearray()
    header += struct.pack("B", 0x03)
    header += struct.pack("BBB", today.year - 1900, today.month, today.day)
    header += struct.pack("<I", n)
    header_len = 32 + 32 * len(fields) + 1
    record_len = 1 + sum(f[2] for f in fields)
    header += struct.pack("<H", header_len)
    header += struct.pack("<H", record_len)
    header += b"\x00" * 20

    for name, ftype, flen, fdec in fields:
        fd = name.encode("ascii")[:10].ljust(11, b"\x00")
        fd += ftype.encode("ascii")
        fd += b"\x00" * 4
        fd += struct.pack("B", flen)
        fd += struct.pack("B", fdec)
        fd += b"\x00" * 14
        header += fd
    header += b"\x0d"

    body = bytearray()
    for row in rows:
        body += b" "  # not deleted
        for (name, ftype, flen, fdec), val in zip(fields, row):
            if ftype == "C":
                s = str(val)[:flen].ljust(flen)
            else:  # numeric
                if fdec > 0:
                    s = f"{val:.{fdec}f}"[:flen].rjust(flen)
                else:
                    s = f"{int(val)}"[:flen].rjust(flen)
            body += s.encode("ascii")
    body += b"\x1a"

    with open(path_base + ".dbf", "wb") as f:
        f.write(header)
        f.write(body)


def write_prj(path_base, wkt):
    with open(path_base + ".prj", "w") as f:
        f.write(wkt)


def write_point_shapefile(path_base, xs, ys, fields, rows, prj_wkt=None):
    write_point_shp_shx(path_base, xs, ys)
    write_dbf(path_base, fields, rows)
    if prj_wkt:
        write_prj(path_base, prj_wkt)
