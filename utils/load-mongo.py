import pymongo
import csv

dbName = 'phraseSuggesting'
connect = 'mongodb://localhost:27017/'
uniFile = 'unigrams.csv'
biFile = 'bigrams.csv'
batchSize = 10000
biWords = 100000
skipUnigramCnt = 1
skipBigramCnt = 1

uniIds = {}
uniCnts = {}


def updateUni(ins, ids):
    words = [v['word'] for v in ins]
    data = dict(zip(words, ids))
    uniIds.update(data)
    cnts = [v['cnt'] for v in ins]
    data = dict(zip(words, cnts))
    uniCnts.update(data)

def loadUnigrams(db):

    db.unigrams.create_index(
        [('cnt', pymongo.DESCENDING)])

    db.unigrams.create_index(
        [('w', pymongo.ASCENDING), ('cnt', pymongo.DESCENDING), ('word', pymongo.ASCENDING)])

    db.unigrams.create_index(
        [('word', pymongo.ASCENDING)])

    id = 0
    with open(uniFile, newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        ins = []
        i = 0
        for row in reader:
            # print(row)

            if int(row[1]) <= skipUnigramCnt:
                continue

            ins.append(
                {'_id': id, 'word': row[0], 'cnt': int(row[1]), 'w': row[0][0]})
            id += 1
            i += 1
            if i > batchSize:
                res = db.unigrams.insert_many(ins)
                updateUni(ins, res.inserted_ids)
                ins = []
                i = 0
                # break

    if i > 0:
        res = db.unigrams.insert_many(ins)
        updateUni(ins, res.inserted_ids)

def loadBigrams(db):
    id = 0
    with open(biFile, newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        ins = []
        i = 0
        for row in reader:
            # print(row)
            ins.append({
                '_id': id,
                'w1': uniIds[row[0]],
                'w2': uniIds[row[1]],
                'cnt': int(row[2]),
                'p': float(float(row[2]) / float(uniCnts[row[0]]))
            })
            id += 1
            i += 1
            if i > batchSize:
                res = db.bigrams.insert_many(ins)
                ins = []
                i = 0
                # break

    if i > 0:
        res = db.bigrams.insert_many(ins)


def loadBigramsGroupped(db):
    ''' пишем в две коллекции, в одной группировка по первому слову, во второй по второму. считаем вероятности'''

    db.forwardBigrams.create_index(
        [('left', pymongo.ASCENDING)])

    db.backwardBigrams.create_index(
        [('right', pymongo.ASCENDING)])

    forwardGroup = {}
    backwardGroup = {}
    with open(biFile, newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if int(row[2]) <= skipBigramCnt:
                continue
            leftId = uniIds[row[0]]
            rightId = uniIds[row[1]]
            pl = float(float(row[2]) / float(uniCnts[row[0]]))
            pr = float(float(row[2]) / float(uniCnts[row[1]])) # вероятность первого по второму слову, т.е. в обратную сторону
            if leftId not in forwardGroup:
                forwardGroup[leftId] = {'left':leftId, 'words':{}}
            forwardGroup[leftId]['words'][rightId] = pl

            if rightId not in backwardGroup:
                backwardGroup[rightId] = {'right':rightId, 'words':{}}
            backwardGroup[rightId]['words'][leftId] = pr

    print('left')

    ins = []
    i = 0
    m = 0
    for id in forwardGroup:
        row = forwardGroup[id]
        if len(row['words']) > m:
            m = len(row['words'])
            print(id, m)
        sort = dict(sorted(row['words'].items(), key=lambda x:x[1], reverse=True))
        row['words'] = list(sort.keys())[0:biWords]
        row['probs'] = list(sort.values())[0:biWords]
        # print(row)
        # return
        ins.append(row)
        i += 1
        if i > batchSize:
            
            res = db.forwardBigrams.insert_many(ins)
            ins = []
            i = 0

    if i > 0:
        res = db.forwardBigrams.insert_many(ins)

    print('right')

    ins = []
    i = 0
    m = 0
    for id in backwardGroup:
        row = backwardGroup[id]
        if len(row['words']) > m:
            m = len(row['words'])
            print(id, m)
        sort = dict(sorted(row['words'].items(), key=lambda x:x[1], reverse=True))
        row['words'] = list(sort.keys())[0:biWords]
        row['probs'] = list(sort.values())[0:biWords]
        ins.append(row)
        i += 1
        if i > batchSize:
            
            res = db.backwardBigrams.insert_many(ins)
            ins = []
            i = 0

    if i > 0:
        res = db.backwardBigrams.insert_many(ins)

with pymongo.MongoClient(connect) as client:

    db = client.get_database(dbName)

    db.unigrams.drop()
    db.forwardBigrams.drop()
    db.backwardBigrams.drop()

    loadUnigrams(db)
    # loadBigrams(db)
    loadBigramsGroupped(db)
