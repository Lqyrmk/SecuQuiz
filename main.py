import pdfplumber
import re


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

    # 处理 replace 映射
    for key in replace_map:
        pdf_text = pdf_text.replace(key, replace_map[key])

    return pdf_text


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
            chapter_match = re.search(r"^第\s*\d+\s*讲", match, re.MULTILINE)
            if chapter_match:
                # 获取到匹配项，即章节编号
                chapter_id = chapter_match.group()
                # 按 id 划分为两部分
                # 取前面部分，即 题目/答案
                item = match.split(chapter_id)[0]
                res.append(item)
                continue

            # 2. 末尾可能包含标题
            title_match = re.search(r"^\d+\.\d+", match, re.MULTILINE)
            if title_match:
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
        return "\n".join(match.strip() for match in res)
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
    question_matches = re.findall(r'(\d+\..+?)(?=\d+\.)', text, flags=re.DOTALL)
    for question_match in question_matches:
        # 去掉题号、开头和结尾的空格、所有换行符
        cleaned_question = re.sub(r'^\d+\.', '', question_match.replace('\n', '').strip())
        # print(f'Question: {cleaned_question}')

        question = cleaned_question.split('A')[0]

        # 对于每个问题，提取选项
        options = []
        # option_matches = re.findall(r'([A-Z]).([^A-Z]+)', cleaned_question)
        option_matches = re.findall(r'[A-Z].[^A-Z]+', cleaned_question)

        # 匹配到了选项
        if option_matches:
            for option_match in option_matches:
                options.append(option_match.strip())  # A.XXXX
        else:
            print(f"没有选项，应为判断题")

        # 封装
        questions.append({
            'question': question,
            'options': options
        })

    return questions

def extract_answer(text):
    return text.strip().replace('\n', ' ').split(' ')

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
