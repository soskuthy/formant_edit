import codecs

def readCSV (fname):
        f = codecs.open(fname, 'r')
        lines = f.readlines()
        f.close()
        header = {}
        table = []
        for l in range(len(lines)):
            fields = lines[l].strip().split("\t")
            if l == 0:
                for c in range(len(fields)):
                    header[fields[c]] = c
            else:
                output_row = []
                for field in fields:
                    if field.startswith('"') and field.endswith('"'):
                        output_row.append(field.replace('"', ''))
                    else:
                        if '.' in field:
                            try:
                                output_row.append(float(field))
                            except:
                                output_row.append(None)
                        else:
                            try:
                                output_row.append(int(field))
                            except:
                                output_row.append(None)
                table.append(output_row)
        return header, table

def writeCSV (fname, header, table):
        text = ["\t".join(header) + "\n"]
        for row in table:
            output_row = ""
            for field in row:
                if isinstance(field, str):
                    output_row += '"' + field + '"' + "\t"
                else:
                    output_row += str(field) + "\t"
            output_row = output_row[:-1] + "\n"
            text.append(output_row)
        f = codecs.open(fname, 'w')
        f.writelines(text)
        f.close()
