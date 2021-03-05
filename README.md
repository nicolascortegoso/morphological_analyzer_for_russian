Алгоритм класса "MostProbableTagSequence" работает на базе разбора морфологического анализатора pymorphy2, чтобы определить более вероятную последовательность тегов для цепочки словоформ.

Pymorphy2 обрабатывает каждую введенную словоформу отдельно и возвращает один или несколько объектов типа "Parse" с информацией о том, как слово может быть разобрано.
Например, для словоформы “крепкие”, “типы”, “стали” pymorphy2 возвращает следующие списки с объектами "Parse":

    morphoanalyzer.parse('крепкие') [
    Parse(word='крепкие', tag=OpencorporaTag('ADJF,Qual plur,nomn'), normal_form='крепкий', score=0.5, methods_stack=((<DictionaryAnalyzer>, 'крепкие', 1393, 20),)), Parse(word='крепкие', tag=OpencorporaTag('ADJF,Qual inan,plur,accs'), normal_form='крепкий', score=0.5, methods_stack=((<DictionaryAnalyzer>, 'крепкие', 1393, 24),))
    ]

    morphoanalyzer.parse('типы') [
    Parse(word='типы', tag=OpencorporaTag('NOUN,inan,masc plur,accs'), normal_form='тип', score=0.5, methods_stack=((<DictionaryAnalyzer>, 'типы', 33, 9),)), Parse(word='типы', tag=OpencorporaTag('NOUN,inan,masc plur,nomn'), normal_form='тип', score=0.25, methods_stack=((<DictionaryAnalyzer>, 'типы', 33, 6),)), Parse(word='типы', tag=OpencorporaTag('NOUN,anim,masc plur,nomn'), normal_form='тип', score=0.25, methods_stack=((<DictionaryAnalyzer>, 'типы', 52, 6),))
    ]

    morphoanalyzer.parse('стали') [
    Parse(word='стали', tag=OpencorporaTag('VERB,perf,intr plur,past,indc'), normal_form='стать', score=0.984662, methods_stack=((<DictionaryAnalyzer>, 'стали', 904, 4),)), Parse(word='стали', tag=OpencorporaTag('NOUN,inan,femn sing,gent'), normal_form='сталь', score=0.003067, methods_stack=((<DictionaryAnalyzer>, 'стали', 13, 1),)), Parse(word='стали', tag=OpencorporaTag('NOUN,inan,femn sing,datv'), normal_form='сталь', score=0.003067, methods_stack=((<DictionaryAnalyzer>, 'стали', 13, 2),)), Parse(word='стали', tag=OpencorporaTag('NOUN,inan,femn sing,loct'), normal_form='сталь', score=0.003067, methods_stack=((<DictionaryAnalyzer>, 'стали', 13, 5),)), Parse(word='стали', tag=OpencorporaTag('NOUN,inan,femn plur,nomn'), normal_form='сталь', score=0.003067, methods_stack=((<DictionaryAnalyzer>, 'стали', 13, 6),)), Parse(word='стали', tag=OpencorporaTag('NOUN,inan,femn plur,accs'), normal_form='сталь', score=0.003067, methods_stack=((<DictionaryAnalyzer>, 'стали', 13, 9),))
    ]

Класс "MostProbableTagSequence" применяет скрытую Марковскую модель и алгоритм Битерви, чтобы выбрать более вероятный "Parse" объект из разбора pymorphy2 для каждой словоформы. Метод класса "get_sequence() принимает как вход массив с результатами морфологического разбора pymorphy2 и возбращает список с наиболее вероятным обьектом "Parse" для каждой словоформы. Например, для таких же словоформ указанных выше, выдает следующий список:

    [
    Parse(word='крепкие', tag=OpencorporaTag('ADJF,Qual plur,nomn'), normal_form='крепкий', score=0.5, methods_stack=((<DictionaryAnalyzer>, 'крепкие', 1393, 20),)), Parse(word='типы', tag=OpencorporaTag('NOUN,inan,masc plur,nomn'), normal_form='тип', score=0.25, methods_stack=((<DictionaryAnalyzer>, 'типы', 33, 6),)), Parse(word='стали', tag=OpencorporaTag('VERB,perf,intr plur,past,indc'), normal_form='стать', score=0.984662, methods_stack=((<DictionaryAnalyzer>, 'стали', 904, 4),)), Parse(word='.', tag=OpencorporaTag('PNCT'), normal_form='.', score=1.0, methods_stack=((<PunctuationAnalyzer>, '.'),))
    ]

Скрытая Марковская модель (СММ) это вероятностная модель последовательности, которая состоит из:
- набора наблюдаемых переменных "Y" (в данном случае, словоформ)
- латентных (скрытых) переменных "X" (в данном случае, частей речи)
Цель модели состоит в том, чтобы определить неизвестные (скрытые) параметры указанной цепочки (частей речи) из наблюдаемых параметров (словоформ).

СММ тренируются на размеченных корпусах OpenCorpora. Для построения модели нужно вычислить два параметра, каждый из которых соответствует некоторой условной вероятности:

вероятности перехода -> q(t|u,v): вероятность появления тега "t" при условии того, что перед ним находятся теги "u" и "v". Вычисляется на основе тегов корпуса, используя части речи. Например: PRED, ADVB, CONJ. Если часть речи меняется по падежам, падежи прикрепляются к ней. Например: NOUN nomn, ADJF accs, PRTF gent. Дополнительные теги: UNKN (неизвестное) LATN (латинская словоформа), NUMB (число) и ROMN (римская цифра). Поскольку, вычисления этого параметра реализирован на базе последовательности три тега, модель называется "триграмной".

вероятности результата -> s(w|t): вероятность того, что тегу "t" соответствует слово "w". В данном случае, не вычисляется на основе корпуса и принимается прямо в том месте вероятность s(t|w) «score» от объекта "Parse" pymorphy2.

Файл "transition_probabilities.json" содержит уже вычисленные вероятности перехода на подкорпусе OpenCorpora со снятой омонимией (предложений: 13277, токенов: 93857, слов: 63306). Скрипт "transition_probabilities.py" позволяет вычислить вероятности переходов используя другой подкорпус OpenCorpora. Процесс вычисления может занимать более одного часа.

Пример применения кода:

        from pymorphy2 import MorphAnalyzer                                 # импортируется класс MorphAnalyzer из pymorphy2
        from hmmtrigram import MostProbableTagSequence                      # импортируется класс MostProbableTagSequence из hmmtrigram

        morph = MorphAnalyzer()                                             # создается экземпляр класса MorphAnalyzer

        token_list = ['крепкие', 'типы', 'стали', '.']                      # любой список токенов

        pymorphy2_analysis = [morph.parse(token) for token in token_list]   # обрабатывается каждая словоформа

        mpts = MostProbableTagSequence('transition_probabilities.json')     # создается экземпляр класса MostProbableTagSequence с файлом вероятностей переходов
        result = mpts.get_sequence(pymorphy2_analysis)                      # вызывается метод класса с массивом набора pymorphy2
        print(result)

Скрипт "test.py" позволяет оценить производительность модели триграмной СММ на основе тестового подкорпуса OpenCorpora. На выходе скрипт создает три файла:
1. (test.txt) содержащий такие предложения, где модель СММ ошиблась хотя бы в одном теге.
2. (hmm_precision_recall_f.csv) включающий оценки accuracy, точность, полноту и F-меру для каждого тега.
3. (pymorphy2_precision_recall_f.csv) включающий такие же оценки при выборе наиболее вероятного тега pymorphy2.




