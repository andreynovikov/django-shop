export function rows(arr, n) {
    /*
    Break a list into ``n`` rows, filling up each row to the maximum equal
    length possible. For example::

        >>> l = range(10)

        >>> rows(l, 2)
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

        >>> rows(l, 3)
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]

        >>> rows(l, 4)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

        >>> rows(l, 5)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

        >>> rows(l, 9)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [], [], [], []]

        # This filter will always return `n` rows, even if some are empty:
        >>> rows(range(2), 3)
        [[0], [1], []]
    */

    let split = Math.trunc(arr.length / n);
    if (arr.length % n != 0)
        split += 1;
    const res = [];
    for (let i = 0; i < n; i++) {
        res.push(arr.slice(split * i, split * (i + 1)));
    }
    return res;
}

export function columns(arr, n) {
    /*
    Break a list into ``n`` columns, filling up each column to the maximum equal
    length possible. For example::

        7x3:
        [[0, 3, 6],
         [1, 4],
         [2, 5]]
        8x3:
        [[0, 3, 6],
         [1, 4, 7],
         [2, 5]]
        9x3:
        [[0, 3, 6],
         [1, 4, 7],
         [2, 5, 8]]
        10x3:
        [[0, 4, 8],
         [1, 5, 9],
         [2, 6],
         [3, 7]]

    Note that this filter does not guarantee that `n` columns will be
    present:
    columns(range(4), 3):
        [[0, 2],
         [1, 3]]
    */

    let split = Math.trunc(arr.length / n);
    if (arr.length % n != 0)
        split += 1;
    const res = [];
    for (let i = 0; i < split; i++) {
        const a = [];
        for (let j = i; j < arr.length; j += split)
            a.push(arr[j]);
        res.push(a);
    }
    return res;
}
