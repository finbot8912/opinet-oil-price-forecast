import pandas as pd

# 지역별 주유소 판매가 시트 확인
df = pd.read_excel("유가변동1.xlsx", sheet_name="5.지역별주유소 판매가", header=None)

print("Sheet dimensions:", df.shape)
print("\nFirst 3 rows:")
for i in range(3):
    row = df.iloc[i]
    print(f"Row {i}:")
    for j in range(min(10, len(row))):
        if pd.notna(row.iloc[j]):
            print(f"  Col {j}: {row.iloc[j]}")
print("\n" + "="*50)

# 실제 데이터가 있는 행 찾기
print("Non-empty rows sample:")
for i in range(min(20, len(df))):
    row = df.iloc[i]
    non_empty_cols = []
    for j in range(min(5, len(row))):
        if pd.notna(row.iloc[j]) and str(row.iloc[j]).strip():
            non_empty_cols.append(f"Col{j}:{row.iloc[j]}")
    if non_empty_cols:
        print(f"Row {i}: {non_empty_cols}")