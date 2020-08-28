# coding=utf-8

import csv
import sys
import pprint
import numpy as np

POSTIT_COLOR_RED = 1
POSTIT_COLOR_BLUE = 2
POSTIT_COLOR_YELLOW = 3
POSTIT_COLOR_OTHER = -1

def edit_csv(input_filename, output_prefix):
    # csv読み込み
    postits = load_csv(input_filename)

    # 色(タイプ)で分ける
    split_postit_groups_by_color = split_by_color(postits)
    yellow_postits = split_postit_groups_by_color[POSTIT_COLOR_YELLOW]

    # y座標(ナラティブフロー(物語の流れ), PBI)で分ける 
    #   TODO: バックボーン(ストーリーの骨格)
    narrative_flows = extract_narrative_flow(yellow_postits)
    pbis = extract_pbi(yellow_postits)

    # ナラティブフローを時系列順にソート
    sorted_narrative_flows = sort_narrative_flow(narrative_flows)
    sorted_narrative_flows = add_index_key(sorted_narrative_flows)

    # x座標から、PBIとナラティブフローを紐付ける
    pbis_with_narrative_flows = relate_narrative_flows_to_pbi(sorted_narrative_flows, pbis)

    # y座標から、PBIを優先度順にソート
    sorted_pbis_with_narrative_flows = sort_pbi_with_narrative_flow(pbis_with_narrative_flows)
    sorted_pbis_with_narrative_flows = add_priority_each_narrative_flow(sorted_pbis_with_narrative_flows)

    # 完成系 : PBIがナラティブフローに紐づけられた状態で、時系列,優先度 順に並んでいる
    write_result(output_prefix, narrative_flows, sorted_pbis_with_narrative_flows)


def load_csv(input_filename):
    with open(input_filename, 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    return rows


def split_by_color(postits):
    result = {
        POSTIT_COLOR_RED : [],
        POSTIT_COLOR_BLUE : [],
        POSTIT_COLOR_YELLOW : [],
        POSTIT_COLOR_OTHER : [],
    }

    for postit in postits:
        color = get_color(postit)
        result[color].append(postit)
    return result


def get_color(postit):
    r, g, b = int(postit['background-r']), int(postit['background-g']), int(postit['background-b'])
    if r == 255 and g == 128 and b == 171:
        return POSTIT_COLOR_RED
    if r == 255 and g == 235 and b == 59:
        return POSTIT_COLOR_YELLOW
    if r == 128 and g == 222 and b == 234:
        return POSTIT_COLOR_BLUE
    return POSTIT_COLOR_OTHER


def extract_narrative_flow(yellow_postits):
    result = []
    for postit in yellow_postits:
        if is_narrative_flow(postit):
            result.append(postit)
    return result


def extract_pbi(yellow_postits):
    result = []
    for postit in yellow_postits:
        if is_pbi(postit):
            result.append(postit)
    return result


def is_narrative_flow(postit):
    return float(postit['y']) < 300


def is_pbi(postit):
    return float(postit['y']) >= 300


def sort_narrative_flow(narrative_flows):
    narrative_flows.sort(
        key=lambda x: (
            float(x['page']),
            float(x['x'])
        )
    )
    return narrative_flows


def add_index_key(dicts):
    for k,x in enumerate(dicts):
        dicts[k]['index'] = k
    return dicts


def relate_narrative_flows_to_pbi(narrative_flows, pbis):
    ...
    for k,pbi in enumerate(pbis):
        target_narrative_flow = search_narrative_flow(pbi, narrative_flows)

        pbis[k]['narrative_flow_index'] = target_narrative_flow['index']
        pbis[k]['narrative_flow_id'] = target_narrative_flow['id']
        pbis[k]['narrative_flow_value'] = target_narrative_flow['value']

    return pbis


def search_narrative_flow(pbi, narrative_flows):
    narrative_flows = exclude_different_page_narrative_flow(pbi, narrative_flows)
    target_narrative_flow = search_nearest_pbi_comparing_x(pbi, narrative_flows)
    return target_narrative_flow


def exclude_different_page_narrative_flow(pbi, narrative_flows):
    return [
        narrative_flow 
        for narrative_flow in narrative_flows 
        if narrative_flow['page'] == pbi['page']]


def search_nearest_pbi_comparing_x(pbi, narrative_flows):
    diff_xs = [
        abs(float(pbi['x']) - float(narrative_flow['x'])) 
        for narrative_flow in narrative_flows
    ]
    min_idx = min(enumerate(diff_xs), key = lambda x:x[1])[0]
    return narrative_flows[min_idx]


def sort_pbi_with_narrative_flow(pbis_with_narrative_flows):
    pbis_with_narrative_flows.sort(
        key=lambda x: (
            float(x['narrative_flow_index']),
            float(x['y'])
        )
    )
    return pbis_with_narrative_flows


def add_priority_each_narrative_flow(pbis_with_narrative_flows):
    pre_narrative_flow_index = '-1'

    priority = 1
    for k,pbi in enumerate(pbis_with_narrative_flows):
        if pre_narrative_flow_index != pbi['narrative_flow_index']:
            priority = 1
            pre_narrative_flow_index = pbi['narrative_flow_index']
        
        pbis_with_narrative_flows[k]['priority_each_narrative_flow'] = priority
        priority += 1
    return pbis_with_narrative_flows


def write_result(output_prefix, narrative_flows, pbis):
    # ユーザストーリーマッピング
    usm = create_usm_2d_list(narrative_flows, pbis)
    with open(output_prefix + 'usm.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(usm)

    # ナラティブフローのリスト
    with open(output_prefix + 'narrative_flow.csv', 'w') as f:
        field_names = narrative_flows[0].keys()
        writer = csv.DictWriter(f, field_names)
        writer.writeheader()
        writer.writerows(narrative_flows)

    # PBIのリスト
    with open(output_prefix + 'pbi.csv', 'w') as f:
        field_names = pbis[0].keys()
        writer = csv.DictWriter(f, field_names)
        writer.writeheader()
        writer.writerows(pbis)



def create_usm_2d_list(narrative_flows, sorted_pbis_with_narrative_flows):
    xsize = len(narrative_flows)
    ysize = max(sorted_pbis_with_narrative_flows, key=lambda x:x['priority_each_narrative_flow'])['priority_each_narrative_flow'] + 1

    result = np.empty((ysize, xsize), dtype=object)

    # header(一番上)にナラティブフロー
    for k, narrative_flow in enumerate(narrative_flows):
        result[0][k] = narrative_flow['value']

    for pbi in sorted_pbis_with_narrative_flows:
        y = int(pbi['priority_each_narrative_flow'])
        x = int(pbi['narrative_flow_index'])
        result[y,x] = pbi['value']

    return result.tolist()



def main():
    if len(sys.argv) < 2:
        input_filename = 'output.csv'
    else:
        input_filename = sys.argv[1]

    if len(sys.argv) < 3:
        output_prefix = 'output_'
    else:
        output_prefix = sys.argv[2]

    edit_csv(input_filename, output_prefix)


if __name__ == "__main__":
    main()