"""Utilities to handle types."""


class hashabledict(dict):
    def as_tuple(self):
        return tuple(sorted(self.items()))

    def __hash__(self):
        return hash(self.as_tuple())

    def __str__(self):
        return str(self.as_tuple())


def test():
    assert hash(hashabledict({'a': 1, 'b': 2})) == hash(
        hashabledict({'b': 2, 'a': 1}))
    adict = hashabledict({'a': 1, 'b': 2})
    assert str(adict) == "(('a', 1), ('b', 2))", f'Got {str(adict)}'


if __name__ == '__main__':
    test()
    print("Tests passed.")
