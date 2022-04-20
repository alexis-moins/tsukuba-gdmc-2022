from gdpc import interface as INTF


class BuildArea:
    def __init__(self, WORLDSLICE):
        self.WORLDSLICE = WORLDSLICE
        self.STARTX, self.STARTY, self.STARTZ, self.ENDX, self.ENDY, self.ENDZ = INTF.requestBuildArea()

