import codecs, csv

def readCSV (fname, delimiter="\t"):
        #f = codecs.open(fname, 'r')
        #lines = f.readlines()
        #f.close()
        header = {}
        table = []
        with codecs.open(fname, 'r') as csvfile:
            lines = csv.reader(csvfile, delimiter=delimiter, quotechar='"')
            l = 0
            for fields in lines:
                if l == 0:
                    for c in range(len(fields)):
                        header[fields[c]] = c
                else:
                    output_row = []
                    for field in fields:
                        # for future: figure out how to detect presence of quotes in orig file 
                        if '.' in field:
                            try:
                                output_row.append(float(field))
                            except:
                                output_row.append(field)
                        else:
                            try:
                                output_row.append(int(field))
                            except:
                                output_row.append(field)
                    table.append(output_row)
                l += 1
        return header, table

def writeCSV (fname, header, table, delimiter="\t"):
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
