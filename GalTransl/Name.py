from typing import Dict, List
import openpyxl
from os.path import join as joinpath, splitext
from GalTransl.CSplitter import SplitChunkMetadata
from GalTransl import LOGGER
from GalTransl.ConfigHelper import CProjectConfig
import csv
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
import asyncio


def load_name_table(name_table_path: str) -> Dict[str, str]:
    """
    This function loads the name table from the given path, supporting both .xlsx and .csv formats.

    Args:
    - name_table_path: The path to the name table (.xlsx or .csv).

    Returns:
    - A dictionary containing the name table.
    """
    name_table: Dict[str, str] = {}
    _, file_extension = splitext(name_table_path)
    file_extension = file_extension.lower()

    try:
        if file_extension == '.xlsx':
            workbook = openpyxl.load_workbook(name_table_path)
            sheet = workbook.active
            
            # Find header row for xlsx
            header = [cell.value for cell in sheet[1]]
            try:
                jp_name_col_idx = header.index('JP_Name')
                cn_name_col_idx = header.index('CN_Name')
            except ValueError:
                LOGGER.warning(f"name替换表 {name_table_path} 缺少 'JP_Name' 或 'CN_Name' 列")
                return name_table

            for row in sheet.iter_rows(min_row=2): # Skip header row
                jp_name = row[jp_name_col_idx].value
                cn_name = row[cn_name_col_idx].value

                # Check if cn_name is not None or empty string
                if jp_name is not None and cn_name is not None and str(cn_name).strip() != "":
                    name_table[str(jp_name)] = str(cn_name)

        elif file_extension == '.csv':
            with open(name_table_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                try:
                    header = next(reader) # Read header row
                except StopIteration:
                    LOGGER.warning(f"CSV name替换表 {name_table_path} 为空或无法读取表头")
                    return name_table
                
                try:
                    jp_name_col_idx = header.index('JP_Name')
                    cn_name_col_idx = header.index('CN_Name')
                except ValueError:
                    LOGGER.warning(f"CSV name替换表 {name_table_path} 缺少 'JP_Name' 或 'CN_Name' 列")
                    return name_table

                for row in reader:
                    if len(row) > max(jp_name_col_idx, cn_name_col_idx):
                        jp_name = row[jp_name_col_idx]
                        cn_name = row[cn_name_col_idx]

                        # Check if cn_name is not None or empty string
                        if jp_name is not None and cn_name is not None and str(cn_name).strip() != "":
                            name_table[str(jp_name)] = str(cn_name)
                    else:
                        LOGGER.warning(f"CSV name替换表 {name_table_path} 中发现格式不正确的行: {row}")
        else:
            LOGGER.warning(f"不支持的 name替换表 文件格式: {file_extension}. 请使用 .xlsx 或 .csv 文件。")
            return name_table
                
    except FileNotFoundError:
        LOGGER.warning(f"name替换表文件未找到: {name_table_path}")
    except Exception as e:
        LOGGER.error(f"加载name替换表 '{name_table_path}' 时出错: {e}")
    return name_table


async def dump_name_table_from_chunks(
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

    # Ask user for export format
    try:
        export_format = await inquirer.select(
            message="请选择导出 name 表的格式:",
            choices=[
                Choice(value="csv", name="CSV (默认)"),
                Choice(value="xlsx", name="Excel (.xlsx)"),
            ],
            default="csv",
        ).execute_async()
    except Exception as e:
        LOGGER.warning(f"无法获取用户输入，将默认使用 CSV 格式: {e}")
        export_format = "csv" # Default to csv if inquirer fails

    file_extension = f".{export_format}"
    output_path = joinpath(proj_dir, f"name替换表{file_extension}")

    try:
        if export_format == 'xlsx':
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

            workbook.save(output_path)
            LOGGER.info(
                f"name已保存到'{output_path}' (Excel格式)，填入CN_Name后可用于后续翻译name字段。"
            )
        elif export_format == 'csv':
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['JP_Name', 'CN_Name', 'Count'])
                # Write data
                for name, count in name_dict.items():
                    writer.writerow([name, gpt_dic.get_dst(name), count])
            LOGGER.info(
                f"name已保存到'{output_path}' (CSV格式)，填入CN_Name后可用于后续翻译name字段。"
            )

    except Exception as e:
        LOGGER.error(f"保存name替换表到 {export_format.upper()} 时出错: {e}")
