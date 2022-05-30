from datetime import datetime
from functools import lru_cache

from gdpc import interface, lookup

__year__ = datetime.now().year

# MODIFIED VERSION OF write book by Blinkenlights from gpdc.toolbox.py
# his version had some problems :
# Automatic line return resulting in lines disappearing from the book


class BookMaker:
    MAX_PAGE = 97  # per book
    MAX_CHARACTERS_PER_PAGE = 255  # per page
    MAX_LINES_PER_PAGE = 14  # per page
    PIXELS_PER_LINE = 100  # default is like 113, but you want to prevent it from making auto return to line

    def __init__(self, content: str, title="Chronicle", author="Blinkenlights",
                 description="I wonder what\\'s inside?", desccolor='gold'):
        self.desccolor = desccolor
        self.description = description
        self.author = author
        self.title = title
        self.content = content
        self.book_data = ""

    @staticmethod
    @lru_cache()
    def word_pixel_length(word):
        """**Return the length of a word based on character width**.

        If a letter is not found, a width of 9 is assumed
        A character spacing of 1 is automatically integrated
        Credits to Blinkenlights for this function!
        """
        return sum([lookup.ASCIIPIXELS[letter] + 1
                    if letter in lookup.ASCIIPIXELS
                    else 10
                    for letter in word]) - 1

    def split_long_line(self, line):
        split = [[]]
        current_line = 0
        current_length = 0  # length in pixels
        for word in line.split():
            # if the word doesn't overflow the line
            word_length = self.word_pixel_length(word) + 3  # + 3 for the space separator between word
            if current_length + word_length < BookMaker.PIXELS_PER_LINE:
                # add it to the current line
                split[current_line].append(word)
                current_length += word_length
            else:
                # otherwise, add it to the next line
                current_line += 1
                current_length = word_length
                split.append([])
                split[current_line].append(word)
        return [' '.join(line) for line in split]

    def create_pages(self, lines):
        pages = [[]]
        current_page = 0
        current_line = 0
        current_length = 0  # length in characters
        for line in lines:
            line_length = len(line) + 3  # for the line return separator
            if current_length + line_length < BookMaker.MAX_CHARACTERS_PER_PAGE \
                    and current_line < BookMaker.MAX_LINES_PER_PAGE:
                pages[current_page].append(line)
                current_line += 1
                current_length += line_length
            else:
                current_page += 1
                current_line = 1
                current_length = line_length
                pages.append([])
                pages[current_page].append(line)
        return pages

    def write_book(self):

        self.book_data = ("{"
                          f'title: "{self.title}", author: "{self.author}", '
                          f'display:{{Lore:[\'[{{"text":"{self.description}",'
                          f'"color":"{self.desccolor}"}}]\']}}, pages:[')

        self.book_data += '\'{"text":"'  # start first page

        lines = self.content.split('\n')
        final_lines = []
        for line in lines:
            final_lines += self.split_long_line(line)

        pages = ['\\\\n'.join(page) for page in self.create_pages(final_lines)]

        # For debug purposes
        # print(f'final lines {final_lines}')
        # print(f'pages {pages}')

        self.book_data += '"}\',\'{"text":"'.join(pages) + '"}\']}'
        return self.book_data


# For test purpose
if __name__ == '__main__':
    text = "Year 1\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n my name is Youri and I hope it will work from " \
           "the first try\n\nYear 2\nI believe I should put on some character here to try to fill up a whole page with " \
           "plain text and see how it react you shouldn\\'t lose a single word !\n\nYear 3\nSo did it worked ?"

    data = BookMaker(text).write_book()
    print(data)

    interface.runCommand("say Hello world")
    interface.runCommand(f'give @a written_book{data}')
