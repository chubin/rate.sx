# vim: encoding=utf-8

import sys
import colored
import itertools

"""

After panela will be ready for it, it will be splitted out in a separate project,
that will be used for all chubin's console services.
There are several features that not yet implemented (see ___doc___ in Panela)

TODO:
    * html output
    * png output

"""

from wcwidth import wcswidth
from colors import find_nearest_color, HEX_TO_ANSI, rgb_from_str
import pyte

# http://stackoverflow.com/questions/19782975/convert-rgb-color-to-the-nearest-color-in-palette-web-safe-color
# pylint: disable=invalid-name

def color_mapping(clr):
    if clr == 'default':
        return None
    return clr

class Point(object):
    """
    One point (character) on a terminal
    """
    def __init__(self, char=None, foreground=None, background=None):
        self.foreground = foreground
        self.background = background
        self.char = char

class Panela:

    """
    To implement:

    Blocks manipulation:

        [*] copy
        [*] crop
        [*] cut
        [*] extend
        [ ] join
        [ ] move
        [*] paste
        [*] strip

    Colors manipulation:

        [*] paint           foreground/background
        [*] paint_line
        [ ] paint_svg
        [ ] fill            background
        [ ] fill_line
        [ ] fill_svg
        [ ] trans

    Drawing:

        [*] put_point
        [*] put_line
        [*] put_circle
        [*] put_rectangle

    Printing and reading:
        ansi            reads vt100 sequence
    """

    def __init__(self, x=80, y=25, panela=None, field=None):

        if panela:
            self.field = [x for x in panela.field]
            self.size_x = panela.size_x
            self.size_y = panela.size_y
            return

        if field:
            self.field = field
            self.size_x = len(field[0])
            self.size_y = len(field)
            return

        self.field = [[Point() for _ in range(x)] for _ in range(y)]
        self.size_x = x
        self.size_y = y

    def in_field(self, col, row):
        if col < 0:
            return False
        if row < 0:
            return False
        if col >= self.size_x:
            return False
        if row >= self.size_y:
            return False
        return True

#
# Blocks manipulation
#

    def copy(self, x1, y1, x2, y2):

        if x1 < 0:
            x1 += self.size_x
        if x2 < 0:
            x2 += self.size_x
        if x1 > x2:
            x1, x2 = x2, x1

        if y1 < 0:
            y1 += self.size_y
        if y2 < 0:
            y2 += self.size_y
        if y1 > y2:
            y1, y2 = y2, y1

        field = [self.field[i] for i in range(y1, y2+1)]
        field = [line[x1:x2+1] for line in field]

        return Panela(field=field)

    def cut(self, x1, y1, x2, y2):
        """
        """
        if x1 < 0:
            x1 += self.size_x
        if x2 < 0:
            x2 += self.size_x
        if x1 > x2:
            x1, x2 = x2, x1

        if y1 < 0:
            y1 += self.size_y
        if y2 < 0:
            y2 += self.size_y
        if y1 > y2:
            y1, y2 = y2, y1

        copied = self.copy(x1, y1, x2, y2)

        for y in range(y1, y2+1):
            for x in range(x1, x2+1):
                self.field[y][x] = Point()

        return copied

    def extend(self, cols=None, rows=None):
        """
        Adds [cols] columns from the right
        and [rows] rows from the bottom
        """
        if cols and cols > 0:
            self.field = [x + [Point() for _ in range(cols)] for x in self.field]
            self.size_x += cols

        if rows and rows > 0:
            self.field = self.field + [[Point() for _ in range(self.size_x)] for _ in range(rows)]
            self.size_y += rows

    def crop(self, left=None, right=None, top=None, bottom=None):
        """
        Crop panela.
        Remove <left>, <right> columns from left or right,
        and <top> and <bottom> rows from top and bottom.
        """

        if left:
            if left >= self.size_x:
                left = self.size_x
            self.field = [x[left:] for x in self.field]
            self.size_x -= left

        if right:
            if right >= self.size_x:
                right = self.size_x
            self.field = [x[:-right] for x in self.field]
            self.size_x -= right

        if top:
            if top >= self.size_y:
                top = self.size_y
            self.field = self.field[top:]
            self.size_y -= top

        if bottom:
            if bottom >= self.size_y:
                bottom = self.size_y
            self.field = self.field[:-bottom]
            self.size_y -= bottom

    def paste(self, panela, x1, y1, extend=False, transparence=False):
        """
        Paste <panela> starting at <x1>, <y1>.
        If <extend> is True current panela space will be automatically extended
        If <transparence> is True, then <panela> is overlayed and characters behind them are seen
        """

        # FIXME:
        #  negative x1, y1
        #  x1,y1 > size_x, size_y

        if extend:
            x_extend = 0
            y_extend = 0
            if x1 + panela.size_x > self.size_x:
                x_extend = x1 + panela.size_x - self.size_x
            if y1 + panela.size_y > self.size_y:
                y_extend = y1 + panela.size_y - self.size_y
            self.extend(cols=x_extend, rows=y_extend)

        for i in range(y1, min(self.size_y, y1+panela.size_y)):
            for j in range(x1, min(self.size_x, x1+panela.size_x)):
                if transparence:
                    if panela.field[i-y1][j-x1].char and panela.field[i-y1][j-x1].char != " ":
                        if panela.field[i-y1][j-x1].foreground:
                            self.field[i][j].foreground = panela.field[i-y1][j-x1].foreground
                        if panela.field[i-y1][j-x1].background:
                            self.field[i][j].background = panela.field[i-y1][j-x1].background
                        self.field[i][j].char = panela.field[i-y1][j-x1].char
                else:
                    self.field[i][j] = panela.field[i-y1][j-x1]

    def strip(self):
        """
        Strip panela: remove empty spaces around panels rectangle
        """

        def left_spaces(line):
            answer = 0
            for elem in line:
                if not elem.char:
                    answer += 1
                else:
                    break
            return answer

        def right_spaces(line):
            return left_spaces(line[::-1])

        def empty_line(line):
            return left_spaces(line) == len(line)

        left_space = []
        right_space = []
        for line in self.field:
            left_space.append(left_spaces(line))
            right_space.append(right_spaces(line))
        left = min(left_space)
        right = min(right_space)

        top = 0
        while top < self.size_y and empty_line(self.field[top]):
            top += 1

        bottom = 0
        while bottom < self.size_y and empty_line(self.field[-(bottom+1)]):
            bottom += 1

        self.crop(left=left, right=right, top=top, bottom=bottom)

#
# Drawing and painting
#

    def put_point(self, col, row, char=None, color=None, background=None):
        """
        Puts charachter with color and background color on the field.
        Char can be a Point or a character.
        """

        if not self.in_field(col, row):
            return
        if isinstance(char, Point):
            self.field[row][col] = char
        else:
            self.field[row][col] = Point(char=char, foreground=color, background=background)

    def put_string(self, col, row, s=None, color=None, background=None):
        """
        Put string <s> with foreground color <color> and background color <background>
        ad <col>, <row>
        """
        for i, c in enumerate(s):
            self.put_point(col+i, row, c, color=color, background=background)

    def put_line(self, x1, y1, x2, y2, char=None, color=None, background=None):
        """
        Draw line (x1, y1) - (x2, y2) fith foreground color <color>, background color <background>
        and charachter <char>, if specified.
        """

        def get_line(start, end):
            """Bresenham's Line Algorithm
            Produces a list of tuples from start and end

            Source: http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm#Python

            >>> points1 = get_line((0, 0), (3, 4))
            >>> points2 = get_line((3, 4), (0, 0))
            >>> assert(set(points1) == set(points2))
            >>> print points1
            [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
            >>> print points2
            [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
            """
            # Setup initial conditions
            x1, y1 = start
            x2, y2 = end
            dx = x2 - x1
            dy = y2 - y1
         
            # Determine how steep the line is
            is_steep = abs(dy) > abs(dx)
         
            # Rotate line
            if is_steep:
                x1, y1 = y1, x1
                x2, y2 = y2, x2
         
            # Swap start and end points if necessary and store swap state
            swapped = False
            if x1 > x2:
                x1, x2 = x2, x1
                y1, y2 = y2, y1
                swapped = True
         
            # Recalculate differentials
            dx = x2 - x1
            dy = y2 - y1
         
            # Calculate error
            error = int(dx / 2.0)
            ystep = 1 if y1 < y2 else -1
         
            # Iterate over bounding box generating points between start and end
            y = y1
            points = []
            for x in range(x1, x2 + 1):
                coord = (y, x) if is_steep else (x, y)
                points.append(coord)
                error -= abs(dy)
                if error < 0:
                    y += ystep
                    error += dx
         
            # Reverse the list if the coordinates were swapped
            if swapped:
                points.reverse()
            return points

        if color and not isinstance(color, basestring):
            color_iter = itertools.cycle(color)
        else:
            color_iter = itertools.repeat(color)

        if background and not isinstance(background, basestring):
            background_iter = itertools.cycle(background)
        else:
            background_iter = itertools.repeat(background)
        
        if char:
            char_iter = itertools.cycle(char)
        else:
            char_iter = itertools.repeat(char)

        for x, y in get_line((x1,y1), (x2, y2)):
            char = next(char_iter)
            color = next(color_iter)
            background = next(background_iter)

            self.put_point(x, y, char=char, color=color, background=background)

    def paint(self, x1, y1, x2, y2, c1, c2=None, bg1=None, bg2=None, angle=None, angle_bg=None):
        """
        Paint rectangle (x1,y1) (x2,y2) with foreground color c1 and background bg1 if specified.
        If spefied colors c2/bg2, rectangle is painted with linear gradient (inclined under angle).
        """

        def calculate_color(i, j):
            if angle == None:
                a = 0
            else:
                a = angle

            r1, g1, b1 = rgb_from_str(c1)
            r2, g2, b2 = rgb_from_str(c2)
            k = 1.0*(j-x1)/(x2-x1)*(1-a)
            l = 1.0*(i-y1)/(y2-y1)*a
            r3, g3, b3 = int(r1 + 1.0*(r2-r1)*(k+l)), int(g1 + 1.0*(g2-g1)*(k+l)), int(b1 + 1.0*(b2-b1)*(k+l))

            return "#%02x%02x%02x" % (r3, g3, b3)

        def calculate_bg(i, j):
            if angle_bg == None:
                a = 0
            else:
                a = angle

            r1, g1, b1 = rgb_from_str(bg1)
            r2, g2, b2 = rgb_from_str(bg2)
            k = 1.0*(j-x1)/(x2-x1)*(1-a)
            l = 1.0*(i-y1)/(y2-y1)*a
            r3, g3, b3 = int(r1 + 1.0*(r2-r1)*(k+l)), int(g1 + 1.0*(g2-g1)*(k+l)), int(b1 + 1.0*(b2-b1)*(k+l))

            return "#%02x%02x%02x" % (r3, g3, b3)

        if c2 == None:
            for i in range(y1,y2):
                for j in range(x1, x2):
                    self.field[i][j].foreground = c1
                    if bg1:
                        if bg2:
                            self.field[i][j].background = calculate_bg(i, j)
                        else:
                            self.field[i][j].background = bg1
        else:
            for i in range(y1,y2):
                for j in range(x1, x2):
                    self.field[i][j].foreground = calculate_color(i, j)
                    if bg1:
                        if bg2:
                            self.field[i][j].background = calculate_bg(i, j)
                        else:
                            self.field[i][j].background = bg1

        return self

    def put_rectangle(self, x1, y1, x2, y2, char=None, frame=None, color=None, background=None):
        """
        Draw rectangle (x1,y1), (x2,y2) using <char> character, <color> and <background> color
        """

        frame_chars = {
            'ascii':    u'++++-|',
            'single':   u'┌┐└┘─│',
            'double':   u'┌┐└┘─│',
        }
        if frame in frame_chars:
            chars = frame_chars[frame]
        else:
            chars = char*6

        for x in range(x1, x2):
            self.put_point(x, y1, char=chars[4], color=color, background=background)
            self.put_point(x, y2, char=chars[4], color=color, background=background)

        for y in range(y1, y2):
            self.put_point(x1, y, char=chars[5], color=color, background=background)
            self.put_point(x2, y, char=chars[5], color=color, background=background)

        self.put_point(x1, y1, char=chars[0], color=color, background=background)
        self.put_point(x2, y1, char=chars[1], color=color, background=background)
        self.put_point(x1, y2, char=chars[2], color=color, background=background)
        self.put_point(x2, y2, char=chars[3], color=color, background=background)


    def put_circle(self, x0, y0, radius, char=None, color=None, background=None):
        """
        Draw cricle with center in (x, y) and radius r (x1,y1), (x2,y2) using <char> character, <color> and <background> color
        """

        def k(x):
            return int(x*1.9)

        f = 1 - radius
        ddf_x = 1
        ddf_y = -2 * radius
        x = 0
        y = radius
        self.put_point(x0, y0 + radius, char=char, color=color, background=background)
        self.put_point(x0, y0 - radius, char=char, color=color, background=background)
        self.put_point(x0 + k(radius), y0, char=char, color=color, background=background)
        self.put_point(x0 - k(radius), y0, char=char, color=color, background=background)
     
        char = "x"
        while x < y:
            if f >= 0: 
                y -= 1
                ddf_y += 2
                f += ddf_y
            x += 1
            ddf_x += 2
            f += ddf_x    
            self.put_point(x0 + k(x), y0 + y, char=char, color=color, background=background)
            self.put_point(x0 - k(x), y0 + y, char=char, color=color, background=background)
            self.put_point(x0 + k(x), y0 - y, char=char, color=color, background=background)
            self.put_point(x0 - k(x), y0 - y, char=char, color=color, background=background)
            self.put_point(x0 + k(y), y0 + x, char=char, color=color, background=background)
            self.put_point(x0 - k(y), y0 + x, char=char, color=color, background=background)
            self.put_point(x0 + k(y), y0 - x, char=char, color=color, background=background)
            self.put_point(x0 - k(y), y0 - x, char=char, color=color, background=background)

    def ansi(self, seq, x=0, y=0, transparence=True):
        """
        Read ANSI sequence and render it to the panela starting from x and y.
        If transparence is True, replace spaces with ""
        """
        screen = pyte.screens.Screen(self.size_x, self.size_y)

        stream = pyte.streams.ByteStream()
        stream.attach(screen)

        stream.feed(seq.replace('\n', '\r\n'))

        for i, line in enumerate(screen.buffer):
            for j, char in enumerate(line):
                self.field[i][j] = Point(char.data, color_mapping(char.fg), color_mapping(char.bg))
                #sys.stdout.write(char.data)
            #sys.stdout.write("\n")

    def __str__(self):
        answer = ""
        skip_next = False
        for i, line in enumerate(self.field):
            for j, c in enumerate(line):
                fg_ansi = ""
                bg_ansi = ""
                stop = ""

                if self.field[i][j].foreground:
                    fg_ansi = '\033[38;2;%s;%s;%sm' % rgb_from_str(self.field[i][j].foreground)
                    stop = colored.attr("reset")

                if self.field[i][j].background:
                    bg_ansi = '\033[48;2;%s;%s;%sm' % rgb_from_str(self.field[i][j].background)
                    stop = colored.attr("reset")

                char = c.char or " "
                if not skip_next:
                    answer += fg_ansi + bg_ansi + char.encode('utf-8') + stop
                skip_next = wcswidth(char) == 2

            # answer += "...\n"
            answer += "\n"
        return answer

def main():

    N = 50

    p = Panela(x=N+1, y=N+1)
    p.put_rectangle(0, 0, 45, 20, frame='single')
    p.put_line(1, 1, 44, 19, char='.')
    p.put_line(1, 19, 44, 1, char='.')
    p.put_circle(22, 10, 8, char='@', color='#ff0000')
    ## p.paint(10, 20, 30, 30, "#ff0000") # , "#220000") # angle=1, bg1='#555555', bg2='#cccccc')

    # for i in range(N):
    #     for j in range(N):
    #         clr = "#00%02x%02x" % (i*5, j*5)
    #         p.put_point(i, j, 'x') # , clr)

    ## p.paint(10, 20, 30, 30, "#ff0000") # , "#220000") # angle=1, bg1='#555555', bg2='#cccccc')

    p.strip()
    sys.stdout.write(str(p))

if __name__ == '__main__':
    main()

# for i in range(N):
#     for j in range(N):
#         clr = "#00%02x%02x" % (i*5, j*5)
#         p.put_point(i, j, 'x') # , clr)

# p.paint(10, 20, 30, 30, "#ff0000") # , "#220000") # angle=1, bg1='#555555', bg2='#cccccc')

#N = 10
#p1 = Panela(x=N, y=N)
#for i in range(N):
#    for j in range(N):
#        clr = "#%02x%02x00" % (200+i*5,200+j*5)
#        p1.put_point(i, j, '.', clr)


#
#for i in range(N):
#    p.put_point(i, 0, '|', "red")
#    p.put_point(i, N, '|', "red")
#    p.put_point(0, i, '-', "red")
#    p.put_point(N, i, '-', "red")
#
#p.put_point(0, 0, '+', "red")
#p.put_point(N, 0, '+', "red")
#p.put_point(0, N, '+', "red")
#p.put_point(N, N, '+', "red")
#
#p.put_line(0, 1, 5, N, 'abc', 'green')
#p.put_line(5, N, 10, 0, 'abc', 'green')


