import pdfplumber
import re


def pdf_to_text(pdf_file):
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
            page_content = text[:end + 1].replace('．', '.').replace('. ', '.').replace('（', '(').replace('）', ')')
            pdf_text += page_content

    return pdf_text


def extract_question(pattern, text):
    """
    获取对应的题目内容
    :param pattern: 正则表达式
    :param text: pdf 文本
    :return: 题目内容
    """

    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        # 取出每个匹配项进行检查
        for i, match in enumerate(matches):
            # 末尾可能包含章节
            chapter_match = re.search(r"^第\s*\d+\s*讲", match, re.MULTILINE)
            if chapter_match:
                # 获取到匹配项，即章节编号
                chapter_id = chapter_match.group()
                # 按 id 划分为两部分
                # 取前面部分，即题目内容
                question = match.split(chapter_id)[0]
                matches[i] = question
                # 不用管后面了
                continue

            # 末尾可能包含标题
            title_match = re.search(r"^\d+\.\d+", match, re.MULTILINE)
            if title_match:
                # 获取到匹配项，即标题编号
                title_id = title_match.group()
                # 按 id 划分为两部分
                # 取前面部分，即题目内容
                question = match.split(title_id)[0]
                matches[i] = question
        # 去掉匹配项两端空白，重组各个匹配项
        result = "\n".join(match.strip() for match in matches)
        return result
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

        # 封装
        questions.append({
            'question': question,
            'options': options
        })

    return questions


if __name__ == '__main__':
    pdf_file = "data/保密知识概论（第二版）练习题2024.pdf"
    pdf_text = pdf_to_text(pdf_file)

    # 使用正则表达式提取题目
    single_choice = extract_question(pattern=r"单项选择题(.*?)判断题", text=pdf_text)
    multiple_choice = extract_question(pattern=r"多项选择题(.*?)单项选择题", text=pdf_text)
    judgement = extract_question(pattern=r"判断题(.*?)多项选择题", text=pdf_text)

    # 提取好的题干和选项
    single_choice_dict = extract_questions_and_options(text=single_choice)
    multiple_choice_dict = extract_questions_and_options(text=multiple_choice)

