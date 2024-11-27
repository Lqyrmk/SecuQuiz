import pdfplumber
import re
import json

from constant import SINGLE_TYPE, MULTI_TYPE, JUDGE_TYPE, ANSWER, QUESTION_TYPE, CONTENT, OPTIONS


def pdf_to_text(pdf_file, replace_map):
    """
    提取 pdf 文件中的文本
    :param pdf_file: 文件列表
    :return: 提取到的文本内容
    """

    pdf_text = ""

    # 打开 PDF 文件
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            # 处理页码
            end = len(text) - 1
            while text[end] >= '0' and text[end] <= '9':
                end -= 1
            pdf_text += text[:end + 1]

    # 处理 replace 映射，统一符号
    for key in replace_map:
        pdf_text = pdf_text.replace(key, replace_map[key])

    # 处理题目编号后的顿号
    pdf_text = re.sub(r"([A-Za-z\d])、([^A-Za-z\d])", r"\1.\2", pdf_text)
    # 在选项id前加井号，方便正则表达式分离选项和二级标题
    pdf_text = re.sub(r'(?<=\n)(?=\d+\.)', '#', pdf_text, flags=re.DOTALL)
    # pdf_text = re.sub(r'(?<=\n)(?=\d+\.\d+)', '#', pdf_text, flags=re.DOTALL)

    # print(pdf_text)

    pdf_text = pdf_text.replace('\n', '')  # 直接清空换行符

    # 加上一个标识符，用于匹配最后一道单选题
    return pdf_text + '判断题'


def extract_item(pattern, text):
    """
    获取对应的题目或答案
    :param pattern: 正则表达式
    :param text: pdf 文本
    :return: 题目内容
    """

    matches = re.findall(pattern, text, re.DOTALL)
    # print(f"matches: {matches}")  # 是一个元组，第 0 个元素是我们要的

    if matches:
        # 结果集
        res = []
        # 取出每个匹配项进行检查
        for i, (match, _) in enumerate(matches):
            # 1. 末尾可能包含章节
            # chapter_match = re.search(r"^第\s*\d+\s*讲", match, re.MULTILINE)
            chapter_match = re.search(r"第\s*\d+\s*讲", match, re.DOTALL)
            if chapter_match:
                # print(f"验证章节chapter_match：{chapter_match}")
                # 获取到匹配项，即章节编号
                chapter_id = chapter_match.group()
                # 按 id 划分为两部分
                # 取前面部分，即 题目/答案
                item = match.split(chapter_id)[0]
                res.append(item)
                continue

            # 2. 末尾可能包含标题
            # 如：1.6 保守国家秘密是公民的义务”
            # 开头是 #数字.数字，并且后面不会出现括号
            # title_match = re.search(r"^\d+\.\d+ [^\d()]+$", match, re.MULTILINE)
            title_match = re.search(r"#\d+\.\d+[^\(\)]+(?!.*[()])$", match, re.DOTALL)
            # 废弃了：
            # title_match = re.search(r"^\d+\.\d+", match, re.MULTILINE)
            if title_match:
                # print(f"验证标题title_match：{title_match}")
                # 获取到匹配项，即标题编号
                title_id = title_match.group()
                # 按 id 划分为两部分
                # 取前面部分，即 题目/答案
                item = match.split(title_id)[0]
                res.append(item)
                continue

            # 3. 无事发生，直接作为结果
            res.append(match)
        # 去掉匹配项两端空白，重组各个匹配项
        # return "\n".join(match.strip() for match in res)
        return '\n'.join(res)
    else:
        print("未找到匹配内容")


def extract_questions_and_options(text):
    """
    提取选择题中的题干和选项
    :param text: 选择题文本
    :return: 提取好的题干和选项
    """

    # 将每个问题和选项分开
    questions = []
    # 用正则表达式匹配题干（数字加点的形式）和选项（A、B、C等）
    # question_matches = re.findall(r'(\d+\..+?)(?=\d+\.)', text, flags=re.DOTALL)
    # question_matches = re.findall(r'(#\d+\..+?\).+?)(?=#\d+\.)', text, flags=re.DOTALL)
    question_matches = re.split(r'(?=#\d+\.)', text)[1:]
    for question_match in question_matches:
        # 去掉空格
        cleaned_question = question_match.strip()

        # 分离题干出来
        question = cleaned_question.split('A')[0]

        # 对于每个问题，提取选项
        options = []
        option_matches = re.findall(r'[A-Z].[^A-Z]+', cleaned_question)

        # 匹配到了选项
        if option_matches:
            for option_match in option_matches:
                options.append(option_match.strip())  # A.XXXX

        # 封装
        questions.append({
            CONTENT: question,
            OPTIONS: options
        })
    return questions

def extract_answer(text):
    return text.strip().replace('\n\n', ' ').replace('\n', ' ').split(' ')

def convert_content_to_json(questions, answers, type):
    # 断言二者对齐
    assert len(questions) == len(answers)
    print(f"{len(questions)} == {len(answers)}")
    # 将答案嵌入到题目信息中
    for question, answer in zip(questions, answers):
        question[ANSWER] = answer
        question[QUESTION_TYPE] = type

    # 将字典保存为JSON格式
    with open(f'./data/quiz_data_{type}.json', 'w') as f:
        json.dump(questions, f)

    num_questions = len(questions)

    if type == SINGLE_TYPE:
        print(f"单项选择题数量：{num_questions}")
    elif type == MULTI_TYPE:
        print(f"多项选择题数量：{num_questions}")
    else:
        print(f"判断题数量：{num_questions}")

if __name__ == '__main__':

    single_choice_pattern = r"单项选择题(.*?)(多项选择题|判断题)"
    multiple_choice_pattern = r"多项选择题(.*?)(单项选择题|判断题)"
    judgement_pattern = r"判断题(.*?)(多项选择题|单项选择题)"

    question_pdf_file = "data/保密知识概论（第二版）练习题2024.pdf"
    answer_pdf_file = "data/保密知识概论（第二版）练习题参考答案2024.pdf"

    question_replace_map = {
        '．': '.',
        '. ': '.',
        '（': '(',
        '）': ')',
        '2归口组织': '2.归口组织',  # 不好处理，直接映射
    }
    answer_replace_map = {
        '○': 'T',
        '×': 'F',
    }

    # 1. 处理问题
    question_pdf_text = pdf_to_text(pdf_file=question_pdf_file, replace_map=question_replace_map)

    # 使用正则表达式提取题目
    single_choice_que = extract_item(pattern=single_choice_pattern, text=question_pdf_text)
    multiple_choice_que = extract_item(pattern=multiple_choice_pattern, text=question_pdf_text)
    judgement_que = extract_item(pattern=judgement_pattern, text=question_pdf_text)

    # 提取最终形式的题干和选项
    single_choice_que = extract_questions_and_options(text=single_choice_que)
    multiple_choice_que = extract_questions_and_options(text=multiple_choice_que)
    judgement_que = extract_questions_and_options(text=judgement_que)

    # 2. 处理答案
    answer_pdf_text = pdf_to_text(answer_pdf_file, answer_replace_map)

    # 使用正则表达式提取答案
    single_choice_ans = extract_item(pattern=single_choice_pattern, text=answer_pdf_text)
    multiple_choice_ans = extract_item(pattern=multiple_choice_pattern, text=answer_pdf_text)
    judgement_ans = extract_item(pattern=judgement_pattern, text=answer_pdf_text)

    # 提取最终形式的答案
    single_choice_ans = extract_answer(text=single_choice_ans)
    multiple_choice_ans = extract_answer(text=multiple_choice_ans)
    judgement_ans = extract_answer(text=judgement_ans)

    # 将题目和答案合并，转为 JSON 格式存储
    convert_content_to_json(single_choice_que, single_choice_ans, type=SINGLE_TYPE)
    convert_content_to_json(multiple_choice_que, multiple_choice_ans, type=MULTI_TYPE)
    convert_content_to_json(judgement_que, judgement_ans, type=JUDGE_TYPE)
