# coding=utf-8

from bs4 import BeautifulSoup
import re
import csv
import sys

def make_csv(input_filename, output_filename = 'output.csv'):
    with open(input_filename, 'r') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # 書き込み先ファイル
    with open(output_filename, 'w') as f:

        # ヘッダー追加
        field_names = ['id', 'page', 'value', 'background-r', 'background-g', 'background-b', 'x', 'y']
        writer = csv.DictWriter(f, field_names)
        writer.writeheader()

        # ページごとに分けるためにまずフレームに分ける
        frames = soup.find_all(class_="jam-frame-container")
        print(len(frames))

        for frame_idx, frame in enumerate(frames):
            postits = frame.find_all(class_="jam-postit-element jam-text-element jam-element goog-control jam-text-element-textproperties")
            print(len(postits))

            for postit in postits:
                postit_data = parse_postit_data(postit)
                postit_data['page'] = frame_idx
                writer.writerow(postit_data)

def parse_postit_data(postit):
    points = parse_translate(postit)

    return {
        'id' : postit['data-element-id'],
        'value' : postit['data-value'],
        'background-r' : postit['data-background-r'],
        'background-g' : postit['data-background-g'],
        'background-b' : postit['data-background-b'],
        'x' : points[0],
        'y' : points[1],
    }

def parse_translate(postit):
    transform_pattern = r'transform: translateX\(\d+.\d+px\) translateY\(\d+.\d+px\)'
    decimal_pattern = r'\d+.\d+'

    style = postit['style']
    match_transform = re.search(transform_pattern, style)
    if match_transform is None:
        return [-1, -1]

    transform = match_transform.group(0)
    points = re.findall(decimal_pattern, transform)
    return points

def main():
    if len(sys.argv) < 2:
        print("Please input input_filename to command line args : python main.py [input_filename] ([output_filename])")
        return

    input_filename = sys.argv[1]

    if len(sys.argv) < 3:
        make_csv(input_filename)
    else:
        output_filename = sys.argv[2]
        make_csv(input_filename, output_filename)

if __name__ == "__main__":
    main()
