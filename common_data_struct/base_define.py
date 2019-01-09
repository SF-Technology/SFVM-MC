# __author__ =  ""


class Base(object):

    def to_json(self):
        json_resp = {}
        result = vars(self)
        for i in result.items():
            if isinstance(i[1],Base):
                json_resp[i[0]] = i[1].to_json()
            elif type(i[1]) == list:
                _tmp = []
                for j in i[1]:
                    _json = None
                    if hasattr(j, 'to_json'):
                        _json = j.to_json()
                    else:
                        _json = j
                    _tmp.append(_json)

                json_resp[i[0]] = _tmp
            else:
                json_resp[i[0]] = i[1]
        return json_resp
