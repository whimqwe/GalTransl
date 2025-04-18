from typing import Dict, List
import openpyxl
from os.path import join as joinpath
from GalTransl.CSplitter import SplitChunkMetadata
from GalTransl import LOGGER
from GalTransl.ConfigHelper import CProjectConfig


def load_name_table(name_table_path: str) -> Dict[str, str]:
    """
    This function loads the name table from the given path.

    Args:
    - name_table_path: The path to the name table.

    Returns:
    - A dictionary containing the name table.
    """
    name_table: Dict[str, str] = {}
    try:
        workbook = openpyxl.load_workbook(name_table_path)
        sheet = workbook.active
        
        # Find header row
        header = [cell.value for cell in sheet[1]]
        try:
            jp_name_col = header.index('JP_Name') + 1
            cn_name_col = header.index('CN_Name') + 1
        except ValueError:
            LOGGER.warning(f"name替换表 {name_table_path} 缺少 'JP_Name' 或 'CN_Name' 列")
            return name_table

        for row in sheet.iter_rows(min_row=2): # Skip header row
            jp_name_cell = sheet.cell(row=row[0].row, column=jp_name_col)
            cn_name_cell = sheet.cell(row=row[0].row, column=cn_name_col)

            jp_name = jp_name_cell.value
            cn_name = cn_name_cell.value

            # Check if cn_name is not None or empty string
            if jp_name is not None and cn_name is not None and str(cn_name).strip() != "":
                name_table[str(jp_name)] = str(cn_name)
                
    except FileNotFoundError:
        LOGGER.warning(f"name替换表文件未找到: {name_table_path}")
    except Exception as e:
        LOGGER.error(f"加载name替换表时出错: {e}")
    return name_table


def dump_name_table_from_chunks(
    chunks: List[SplitChunkMetadata], proj_config: CProjectConfig
):
    name_dict = {}
    proj_dir = proj_config.getProjectDir()
    gpt_dic=proj_config.gpt_dic

    for chunk in chunks:
        for tran in chunk.trans_list:
            if tran.speaker and isinstance(tran.speaker, str):
                if tran.speaker not in name_dict:
                    name_dict[tran.speaker] = 0
                name_dict[tran.speaker] += 1

    name_dict = dict(sorted(name_dict.items(), key=lambda item: item[1], reverse=True))

    LOGGER.debug(f"共发现 {len(name_dict)} 个人名，按出现次数排序如下：")
    for name, count in name_dict.items():
        LOGGER.debug(f"{name}: {count}")

    excel_path = joinpath(proj_dir, "name替换表.xlsx")
    try:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "NameTable"

        # Write header
        sheet['A1'] = 'JP_Name'
        sheet['B1'] = 'CN_Name'
        sheet['C1'] = 'Count'

        # Write data
        row_num = 2
        for name, count in name_dict.items():
            sheet[f'A{row_num}'] = name
            sheet[f'B{row_num}'] = gpt_dic.get_dst(name)
            sheet[f'C{row_num}'] = count
            row_num += 1

        workbook.save(excel_path)
        LOGGER.info(
            f"name已保存到'{excel_path}'，填入CN_Name后可用于后续翻译name字段。"
        )
    except Exception as e:
        LOGGER.error(f"保存name替换表到Excel时出错: {e}")
