import json
import random
from collections import defaultdict

import quiz_utils

from constant import SINGLE_TYPE, MULTI_TYPE, JUDGE_TYPE, TYPE_MAPPING, VISUAL_ID, CONTENT, OPTIONS, ANSWER, QUESTION_TYPE, \
    YES_SET

"""刷题脚本"""

class Question(object):

    def __init__(self, meta_data: dict) -> None:
        # 解析元数据
        self.visual_id = meta_data[VISUAL_ID]
        self.content = meta_data[CONTENT]
        self.options = meta_data[OPTIONS]
        self.answer = meta_data[ANSWER]
        self.type = meta_data[QUESTION_TYPE]

        # 用户的直接回答
        self.direct_answer = ''
        self.direct_answer_detail = ''
        # 用于校验的回答
        self.validation_answer = ''

        # 用户可见的选项
        self.visual_options_str = ''
        # “新选项 -> 旧选项” 映射，用于对答案
        self.options_mapping = defaultdict(str)

        # 用户可见的答案
        self.visual_answer = ''
        self.visual_answer_detail = ''

        if self.type == JUDGE_TYPE:
            # 判断题的可见答案和真实答案是统一的
            # 且不用处理选项
            self.visual_answer = self.visual_answer_detail = self.answer
        else:
            # 选择题需要预处理选项和答案
            self.process_options_and_answer()

    def process_options_and_answer(self):
        # 打乱选项
        random.shuffle(self.options)
        # 在逻辑中处理用户可见形式的答案
        visual_answer = ''
        visual_answer_detail = []
        for i, info in enumerate(self.options):
            option = chr(i + ord('A'))  # 新选项
            self.options_mapping[option] = info  # 旧选项
            # 根据 旧选项是否为答案 得出 新选项是否为答案
            if info[0] in self.answer:  # 'ABCD'
                visual_answer += option  # 新选项
                visual_answer_detail.append(option + info[1:])  # 新选项 拼上 旧选项内容

        # print(self.visual_answer)
        # 按顺序处理的，所以答案已经排好序了
        self.visual_answer = visual_answer
        self.visual_answer_detail = '\n'.join(visual_answer_detail)

        # 在 Python 3.7 及以上版本中，keys() 返回的键是有序的，即插入顺序
        # 这里插入顺序正好是按字母顺序
        for c, option in self.options_mapping.items():
            self.visual_options_str += f'{c}. {option[2:]}\n'

    def answer_question(self, ans_options: str) -> bool:
        # 去掉空白，改大写
        ans_options = ans_options.strip().replace(' ', '').upper()
        # 确定题型
        if self.type == JUDGE_TYPE:
            # 判断题，输入即答案，如果有多个输入，选择其中第一个
            self.direct_answer = ans_options[0]
            self.direct_answer_detail = ans_options[0]
            self.validation_answer = ans_options[0]
        else:
            # 排序一下就是直接回答
            self.direct_answer = ''.join(sorted(ans_options))
            direct_answer_detail = [option + self.options_mapping[option][1:] for option in self.direct_answer]
            self.direct_answer_detail = '\n'.join(direct_answer_detail)
            # 获取真实选项信息
            options = [self.options_mapping[ans_option] for ans_option in ans_options]
            # 获取真实选项
            options = [option.split('.')[0] for option in options]
            options.sort()
            # 排序，重组
            self.validation_answer = ''.join(options)
        # 对答案
        return self.validation_answer == self.answer

    def __str__(self):
        return f"{self.visual_id}. {self.content.split('.')[1]} ({TYPE_MAPPING[self.type]})\n{self.visual_options_str}\n"


def load_questions_and_answers(type):
    with open(f'../data/quiz_data_{type}.json', 'r') as f:
        quiz_data = json.load(f)
    print(f"{TYPE_MAPPING[type]} {len(quiz_data)} 道")
    return quiz_data


def generate_questions(quiz_data, num_questions):
    # 题目集合
    questions = set()
    # 生成 num_question 道不重复的题目
    while len(questions) < num_questions:
        # 生成一个在 0 到 m - 1 之间的随机整数，
        question_id = random.randint(0, m - 1)
        questions.add(question_id)

    # 正确率计数
    correct_cnt = 0
    # 获取对应的题目数据
    for i, question_id in enumerate(questions, start=1):
        question_data = quiz_data[question_id]
        question_data[VISUAL_ID] = i
        # 初始化对象
        question = Question(question_data)
        # 打印题目
        print(question)
        ans_options = input('请输入答案（判断题请用 T 或 F 表示）：')
        if question.answer_question(ans_options):
            correct_cnt += 1
            print(f"\n回答正确！答案为 {question.visual_answer_detail}\n")
        else:
            print(f"\n回答错误！\n你的答案为：{question.direct_answer}")
            if question.type != JUDGE_TYPE:
                print(f"{question.direct_answer_detail}\n")
            print(f"正确答案为：{question.visual_answer}")
            if question.type != JUDGE_TYPE:
                print(f"{question.visual_answer_detail}\n")

        # input('按回车键继续...')
        # 清空控制台

    print(f"本轮作答完毕，正确作答个数：{correct_cnt}，"
          f"错误作答个数：{num_questions - correct_cnt}，"
          f"你的正确率为：{100 * correct_cnt / num_questions}%")



if __name__ == '__main__':

    # 从 JSON 文件提取字典
    single_choice_data = load_questions_and_answers(SINGLE_TYPE)
    multiple_choice_data = load_questions_and_answers(MULTI_TYPE)
    judgement_choice_data = load_questions_and_answers(JUDGE_TYPE)

    quiz_data = single_choice_data + multiple_choice_data + judgement_choice_data
    m = len(quiz_data)
    print(f"题库题目总数为：{m}\n")

    while True:
        num_questions = int(input('请输入测试题目数量：'))
        if num_questions == 0:
            break
        # 生成题目
        generate_questions(quiz_data, num_questions)
        # 下一轮
        continue_option = input('是否继续新一轮作答？\n输入 y (yes) 或 n (no)：')
        if continue_option.upper() not in YES_SET:  # no
            break
        # quiz_utils.clear_console()

    print('再见！')