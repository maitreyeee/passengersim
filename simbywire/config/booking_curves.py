#                     name = str(z[1]).strip()
#                     curve = airsim_utils.parse_array(z[2:])
#                     bc = BookingCurve(name)
#                     self.curves[name] = bc
#                     for _dcp, _pct in zip(self.dcps, curve):
#                         bc.add_dcp(int(_dcp), float(_pct))


from .named import Named


class BookingCurve(Named, extra="forbid"):
    curve: dict[int, float]
