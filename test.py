from bs4 import BeautifulSoup
import pymorphy2
from os import system, name
import json
import re
import csv
from sklearn.metrics import multilabel_confusion_matrix

# набор подкорпусов
available_subcorpus = {'1': ('со снятой омонимией', 'предложений: 13277, токенов: 93857, слов: 63306', 'annot.opcorpora.no_ambig.xml'), '2':('со снятой омонимией без UNKN', 'предложений: 10961, токенов: 72619, слов: 50397', 'annot.opcorpora.no_ambig_strict.xml')}
selected_subcorpus = False


with open('transition_probabilities.json') as json_file:
	data = json.load(json_file)

def clear():
	# for windows
	if name == 'nt':
		_ = system('cls')
	# for mac and linux(here, os.name is 'posix')
	else:
		_ = system('clear') 


# набор главных тегов opencorpora
open_corpora_tag_set = ['NOUN', 'ADJF', 'ADJS', 'COMP', 'VERB', 'INFN', 'PRTF', 'PRTS', 'GRND', 'NUMR', 'ADVB', 'NPRO', 'PRED', 'PREP', 'CONJ', 'PRCL', 'INTJ', 'NUMB', 'UNKN', 'LATN', 'ROMN']

# существительные
mark_as_sustantives = ['NUMB', 'LATN', 'ROMN', 'HANI', 'GREK', 'TIME', 'DATE']

# не учитаемые токены 
tokens_to_ignore = ['PNCT', 'SYMB']

# граммемы pymorphy2
case = ['nomn','gent','datv','accs','ablt','loct','voct','gen1', 'gen2','acc2', 'loc1', 'loc2']

grams_to_add = open_corpora_tag_set + case + mark_as_sustantives


morph = pymorphy2.MorphAnalyzer()

def tokenization(sentence):
	formated_sentence = list(filter(lambda x: x != "", re.split(r'\W', sentence)))
	return formated_sentence


def morphoanalysis(token_list):
	sentence = []
	for token in token_list:
		p = morph.parse(token)
		token_info = [token, []]
		for i in p:
			lemma = i.normal_form
			score = i.score
			pos = i.tag.POS
			if pos is None:
				pos = i.tag._POS
			case = i.tag.case
			l = [lemma, score]
			if case is None:
				pos_case = pos
			else:
				pos_case = '{} {}'.format(pos, case)
			info = [lemma, score, str(pos_case), str(i.tag)]
			token_info[1].append(info)
		sentence.append(token_info)
	return sentence


def desambiguate(tagged_tokens):
	error_in_desambiguation_process = False
	desambiguated_sentence = []
	token_counter = 1
	end_of_sentence = ['конец предложения', [['<E>',1, '<E>']]]
	tagged_tokens.append(end_of_sentence)

	previous_states = [{'<S>': [1, '<*>']}]
	
	for token in tagged_tokens:
		current_states = []
		previous_nodes = previous_states[-1]

		dict_pos = {}
		token_counter += 1
		for pos in token[1]:
			t = pos[2]
			dict_pos[t] = [0, 'UNKN']
			
			for key,value in previous_states[-1].items():
				previous_state_prob = value[0]
				emission_prob = pos[1]
				u_v = '{}_{}'.format(value[1],key)
				transition_prob = data[t][u_v]
				probability = previous_state_prob * emission_prob * transition_prob
				if probability > dict_pos[t][0]:
					dict_pos[t][0] = probability
					dict_pos[t][1] = key
		previous_states.append(dict_pos)
	
	highest_score = '<E>'
	desambiguated_tag_list = []
	for i in previous_states[::-1]:
		try:
			highest_score = i[highest_score][1]
			desambiguated_tag_list.append(highest_score)
		except:
			error_in_desambiguation_process = True
		
	for i, token in enumerate(tagged_tokens[:-1]):
		tup = (token[0], desambiguated_tag_list[::-1][i+2])
		desambiguated_sentence.append(tup)

	return desambiguated_sentence


# интерфейс для выбора подкорпуса
clear()
print('Эксперимент снятия неоднозначности для разметки части речи pymorphy2 при помощи СММ (скрытой марковской модели)\n')
print('Выберите номер подкорпуса для тестирования и нажмите "Enter"')
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


print('Словоформы подкорпуса размечаются. Подождите пожалуйста...\n')

if selected_parameters:
	# извлекаем словоформ и часть речи из подкорпуса
	subcorpus = []
	soup = BeautifulSoup(open(selected_subcorpus), 'html.parser')
	for sentence in soup.find_all('sentence'):
		sent = []
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
						print(token)
					t = grammemes[0]
				token_pos = (token, t)
				sent.append(token_pos)
			elif grammemes[0] in tokens_to_ignore + mark_as_sustantives: # None -> если использованного тега нет в наборе тегов Opencorpora
				pass
		subcorpus.append(sent)


tag_counter = 0
wrong_tagged_desambiguated = 0
wrong_tagged_pymorphy_most_probable = 0

label_list = ['ADJF ablt','ADJF accs','ADJF datv','ADJF gent','ADJF loct','ADJF nomn','ADJS','ADVB','COMP','CONJ','GRND','INFN','INTJ','LATN','NOUN ablt','NOUN accs','NOUN datv','NOUN gen2','NOUN gent','NOUN loc2','NOUN loct','NOUN nomn','NOUN voct','NPRO ablt','NPRO accs','NPRO datv','NPRO gent','NPRO loct','NPRO nomn','NUMB','NUMR ablt','NUMR accs','NUMR datv','NUMR gent','NUMR loct','NUMR nomn','PRCL','PRED','PREP','PRTF ablt','PRTF accs','PRTF datv','PRTF gent','PRTF loct','PRTF nomn','PRTS','ROMN','UNKN','VERB']

true_labels = []
predicted_pymorphy2 = []
predicted_hmm = []

file_name = 'test.txt'

with open(file_name, 'w') as out_file:
	detail = 'Неправильно размеченные предложения скытой марковской моделей на основе тегов pymorphy2:\n\n'
	problem = 'Проблемы при обработке со следующими предложениями:\n\n'
	for sentence in subcorpus:
		right_tagged = True
		tokens = [word[0] for word in sentence]
		tagged_tokens = morphoanalysis(tokens)
		try:
			desambiguated_sentence = desambiguate(tagged_tokens)
			for i, tag in enumerate(sentence):
				tag_counter += 1
				pymorphy_most_probable_tag = tagged_tokens[i][1][0][2]
				true_labels.append(tag[1])
				predicted_pymorphy2.append(pymorphy_most_probable_tag)
				predicted_hmm.append(desambiguated_sentence[i][1])
				if tag[1] != pymorphy_most_probable_tag:
					wrong_tagged_pymorphy_most_probable += 1
				if tag[1] != desambiguated_sentence[i][1]:
					right_tagged = False
					wrong_tagged_desambiguated += 1
			if right_tagged == False:
				detail += 'OpenCorpora теги: '
				detail += ' '.join([str(i) for i in sentence])
				detail += '\nСММ выбраны теги: '
				detail += ' '.join([str(i) for i in desambiguated_sentence])
				detail += '\n\n'
		except:
			problem += ' '.join([str(i) for i in sentence])
			problem  += '\n'
	totals = 'Результаты:\n\n'
	totals += 'Количество размеченных словоформ: {}\n'.format(tag_counter)
	totals += 'Количество неправильно размеченных словоформ при выборе наиболее вероятного тега pymorphy2: {}\n'.format(wrong_tagged_pymorphy_most_probable)
	totals += 'Количество неправильно размеченных на основе наиболее вероятной последовательности тегов: {}\n'.format(wrong_tagged_desambiguated)
	totals += 'Точность при выборе наиболее вероятного тега pymorphy2: {}\n'.format(100 - (wrong_tagged_pymorphy_most_probable/tag_counter) * 100)
	totals += 'Точность наиболее вероятной последовательности тегов: {}\n\n'.format(100 - (wrong_tagged_desambiguated/tag_counter) * 100)
	print(totals)
	out_file.write(totals)
	out_file.write(detail)
	out_file.write(problem)

print('Готово. Более подробные результаты в файле "{}"'.format(file_name))



def divide(numerator, denominator):
	denom = numerator + denominator
	if denom == 0:
		return 0
	else:
		return round(numerator / denom, 2)

def f_1(precision, recall):
	numerator = 2*(precision * recall)
	denominator = precision + recall
	try:
		return round(numerator/denominator,2)
	except:
		return 0

def calculate_precision_recall_f(filename, conf_matrix):
	with open(filename, 'w') as csv_file:
		writer = csv.writer(csv_file)
		writer.writerow(['Tег', 'TN', 'FP (I err)', 'FN (II err)', 'TP', 'Точность', 'Полнота', 'F-мера'])
		precision_list = []
		recall_list = []
		f_list = []
		for i, matrix in enumerate(conf_matrix):
			tp = int(matrix[1][1])
			fp = int(matrix[0][1])
			fn = int(matrix[1][0])
			precision = divide(tp, fp)
			precision_list.append(precision)
			recall = divide(tp, fn)
			recall_list.append(recall)
			f = f_1(precision, recall)
			f_list.append(f)
			writer.writerow([label_list[i], matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1], precision, recall, f])
		average_precision = round(sum(precision_list) / len(precision_list),2)
		average_recall = round(sum(recall_list) / len(recall_list),2)
		average_f = round(sum(f_list) / len(f_list),2)		
		writer.writerow(['Среднее', '', '', '', '', average_precision, average_recall, average_f])


confusion_matrix_pm2 = multilabel_confusion_matrix(true_labels, predicted_pymorphy2, labels=label_list)
calculate_precision_recall_f('pymorphy2_precision_recall_f.csv', confusion_matrix_pm2)

confusion_matrix_hmm = multilabel_confusion_matrix(true_labels, predicted_hmm, labels=label_list)
calculate_precision_recall_f('hmm_precision_recall_f.csv', confusion_matrix_hmm)