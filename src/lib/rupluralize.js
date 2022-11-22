const rupluralize = (value, endings) => {
    if ([11, 12, 13, 14].includes(value % 100))
        return endings[2];
    if (value % 10 === 1)
        return endings[0];
    if ([2, 3, 4].includes(value % 10))
        return endings[1];
    return endings[2];
};

export default rupluralize;
