import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import pymorphy2
import csv
from os import system, name 

def clear():
	# for windows
	if name == 'nt':
		_ = system('cls')
	# for mac and linux(here, os.name is 'posix')
	else:
		_ = system('clear')
		
csv_file = 'transition_probabilities.csv'
json_file = 'transition_probabilities.json'


# набор главных тегов opencorpora
open_corpora_tag_set = ['NOUN', 'ADJF', 'ADJS', 'COMP', 'VERB', 'INFN', 'PRTF', 'PRTS', 'GRND', 'NUMR', 'ADVB', 'NPRO', 'PRED', 'PREP', 'CONJ', 'PRCL', 'INTJ', 'NUMB', 'UNKN', 'LATN', 'ROMN']

# существительные
mark_as_sustantives = ['NUMB', 'LATN', 'ROMN', 'HANI', 'GREK', 'TIME', 'DATE']

# не учитаемые токены 
tokens_to_ignore = ['PNCT', 'SYMB']

inam = ['inam','anim']
gender = ['masc','femn','neut']
number = ['sing','plur']
case = ['nomn','gent','datv','accs','ablt','loct','voct', 'gen1', 'gen2','acc2', 'loc1', 'loc2']

transitivity = ['intr', 'tran']

grams_to_add = open_corpora_tag_set + case + mark_as_sustantives

# набор подкорпусов
available_subcorpus = {'1': ('со снятой омонимией', 'предложений: 13277, токенов: 93857, слов: 63306', 'annot.opcorpora.no_ambig.xml'), '2':('со снятой омонимией без UNKN', 'предложений: 10961, токенов: 72619, слов: 50397', 'annot.opcorpora.no_ambig_strict.xml'))}
selected_subcorpus = False



# функция для вычисления вероятности происхождений
def word_given_tag(word, tag, train_bag):
    tag_list = [pair for pair in train_bag if pair[1]==tag]
    count_tag = len(tag_list)
    w_given_tag_list = [pair[0] for pair in tag_list if pair[0]==word]
    count_w_given_tag = len(w_given_tag_list)
    return (count_w_given_tag, count_tag)


# функция для вычисления вероятности переходов
def t2_given_t1(t2, t1, train_bag):
    tags = [pair[1] for pair in train_bag]
    count_t1 = len([t for t in tags if t==t1])
    count_t2_t1 = 0
    for index in range(len(tags)-1):
        if tags[index]==t1 and tags[index+1] == t2:
            count_t2_t1 += 1
    return (count_t2_t1, count_t1)



# функция для вычисления вероятности переходов
def t_given_uv(t, u, v, train_bag):
    tags = [pair[1] for pair in train_bag] 		#выбераем только теги 
    count_uv = 0
    count_t_uv = 0
    for index in range(len(tags)-1):
        if tags[index]==u and tags[index+1] == v:
            count_uv += 1
    for index in range(len(tags)-2):
        if tags[index]==u and tags[index+1] == v and tags[index+2] == t:
            count_t_uv += 1   
    return (count_t_uv, count_uv)





# интерфейс для выбора подкорпуса
clear()
print('Вычисление вероятностей перехода для частей речи на основе размеченного подкорпуса\n')
print('Выберите номер подкорпуса и нажмите "Enter"')
for k,v in available_subcorpus.items():
	print('[{}] {} ({})'.format(k, v[0], v[1]))
while selected_subcorpus is False:
	subcorpus = input()
	if subcorpus in available_subcorpus.keys():
		selected_subcorpus = available_subcorpus[subcorpus][2]
		print('Выбран подкорпус {} ({})\n'.format(available_subcorpus[subcorpus][0], available_subcorpus[subcorpus][1]))
	else:
		print('Введите цифер между {}'.format(available_subcorpus.keys()))


selected_parameters = ['на основе словоформ', 'token', 'text']

print('Вычисляются вероятности перехода. Подождите пожалуйста несколько секунд...')

if selected_parameters:
	# извлекаем словоформ и часть речи из подкорпуса
	subcorpus = []
	soup = BeautifulSoup(open(selected_subcorpus), 'html.parser')
	for sentence in soup.find_all('sentence'):
		sent = [('<*>', '<*>'), ('<S>', '<S>')]
		for entry in sentence.find_all(selected_parameters[1]):
			token = entry.attrs[selected_parameters[2]]
			grammemes = []
			extra_tag = ''
			for gram in entry.find_all('g'):
				g = gram.attrs['v']
				if g in case:
					if g == 'gen1':
						extra_tag += 'gent'
					elif g == 'loc1':
						extra_tag += 'loct'
					else:		
						extra_tag += g
				grammemes.append(g)
			if grammemes[0] in open_corpora_tag_set: # если использованный тег соответствует набору тегов Opencorpora
				if len(extra_tag) > 0:
					t = '{0} {1}'.format(grammemes[0], extra_tag)
				else:
					if grammemes[0] == 'NOUN':
						print('Осторожно! существительное без падежа ', token)
					t = grammemes[0]
				token_pos = (token, t)
				sent.append(token_pos)
			elif grammemes[0] in tokens_to_ignore + mark_as_sustantives: # None -> если использованного тега нет в наборе тегов Opencorpora
				pass
		end_of_sentence = ('<E>', '<E>')
		sent.append(end_of_sentence)
		subcorpus.append(sent)
	
	# создаем списки обучающих и тестовых слов с POS тегами
	train_tagged_words = [ tup for sent in subcorpus for tup in sent ]							#список кортежов	
	tags = {tag for word,tag in train_tagged_words} # уникальные теги в обучающих данных

combined_tags = ['<*>_<S>']
for u in list(tags):
	if u not in ['<*>', '<E>']:
		for v in list(tags):			
			if v not in ['<*>', '<S>', '<E>'] :
				comb_tag = '{}_{}'.format(u,v)
				combined_tags.append(comb_tag)
	
tags.remove('<S>')
tags.remove('<*>')

tags_matrix = np.zeros((len(combined_tags), len(tags)), dtype='float32')


counter = 1
for i, u_v in enumerate(combined_tags):
	for j, t in enumerate(list(tags)):
		uv = u_v.split('_')
		try:
			probability = t_given_uv(t, uv[0], uv[1], train_tagged_words)[0]/(t_given_uv(t, uv[0], uv[1], train_tagged_words)[1])
		except:
			probability = 0.000000001
		tags_matrix[i, j] = probability 
		print('[{}] t:{} / u:{} x v:{} = {}'.format(counter, t, uv[0], uv[1], probability))
		counter += 1
		if probability > 0:
			tags_matrix[i, j] = probability
		else:
			tags_matrix[i, j] = 0.000000001

		tags_df = pd.DataFrame(tags_matrix, columns = list(tags), index=combined_tags)

tags_df.index = combined_tags
print(tags_matrix.shape)
print(tags_df)
df1_transposed = tags_df.T
df_sorted = df1_transposed.sort_index(axis=1)
df_sorted_index = df_sorted.sort_index()
df_sorted_index.to_csv(csv_file)
tags_df.to_json(json_file)


"""
	

	# создание t x t матрицы перехода тегов, t = количество тегов
	# матрица(i, j) представляет P(j тег после i тега)
	tags_matrix = np.zeros((len(tags), len(tags)), dtype='float32')
	for i, t1 in enumerate(list(tags)):
		for j, t2 in enumerate(list(tags)):
			probability = t2_given_t1(t2, t1, train_tagged_words)[0]/t2_given_t1(t2, t1, train_tagged_words)[1]
			if probability > 0:
				tags_matrix[i, j] = probability
			else:
				tags_matrix[i, j] = 0.000000001
			tags_df = pd.DataFrame(tags_matrix, columns = list(tags), index=list(tags))
	print(tags_df)
	df1_transposed = tags_df.T
	df_sorted = df1_transposed.sort_index(axis=1)
	df_sorted_index = df_sorted.sort_index()
	df_sorted_index.to_csv(csv_file)
	tags_df.to_json(json_file)
"""
	
print('Готово. Созданы файлы {} и {} с вероятностями перехода.'.format(csv_file, json_file))