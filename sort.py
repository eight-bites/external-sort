#запустить: python3 sort.py random_numbers.txt 1000000
"""
Лабораторная работа: внешняя сортировка.
Текстовый файл: одно целое число на строку.
"""

import sys
import os
import heapq
from multiprocessing import Pool,cpu_count


# слияние двух уже отсортированных списков, которые я потом отправляю в саму сортировку
def slit(lev, prav):
    i = 0

    j = 0
    otvet = []
    while i < len(lev ) and j < len(prav):
        if lev[i] <= prav[j]:
            otvet.append(lev[i])
            i += 1
        else:
            otvet.append(prav[j])
            j += 1
    otvet.extend(lev[i:] )
    otvet.extend(prav[j:] )
    return otvet


# сама моя сортировка СЛИЯНИЕМ!!! ( сложность не превышает n(log n)
def sort_mergem(chisla):
#выход из рекурсии
    if len(chisla) <= 1:
        return chisla
    seredina = len(chisla)// 2
    lev = sort_mergem( chisla[:seredina])
    prav = sort_mergem(chisla[seredina:])
    return slit(lev, prav)


# читаем не больше pamyat целых чисел (по одному на строку)
def chitat_kusok(flow, pamyat):
    chisla = []
    while len(chisla) < pamyat:
        stroka = flow.readline()
        if stroka == '':
            break
        stroka = stroka.strip()
        if stroka == '':
            continue
        chisla.append(int(stroka))
    return chisla


# записываем числа обратно в текстовый файл (одно на строку)
def zapisat_txt(put, chisla):
    f = open(put, 'w', encoding='utf-8')
    for x in chisla:
        f.write(str(x) + '\n')
    f.close()


#сортировка одного куска (уже прочитанный список чисел)
def sort_kuska(chisla):
    if not chisla:
        return []
    return sort_mergem(chisla)


#склеимаем отсортированные куски обратно
def skeit_spiski(spiski):
    tek = list(spiski)
    while len(tek) > 1:
        novye = []
        i = 0
        while i < len(tek ):
            if i + 1 < len(tek):
                novye.append(slit(tek[i], tek[i + 1]))
            else:
                novye.append(tek[i])
            i += 2
        tek = novye
    return tek[0]  if tek else []


#распределяем куски списка по ядрам (без seek в файл)
def razbit_po_yadram(chisla, ncpu):
    n = len(chisla)
    ncpu = max(1,min(ncpu, n))
    zadachi = []
    start = 0
    baza = n // ncpu
    ost = n % ncpu

    for i in range(ncpu):
        k = baza
        if i < ost:
            k += 1
        if k > 0:
            zadachi.append(chisla[start:start + k])
            start += k
    return zadachi


# куски обрабатываются в пуле процессов
def obrabotat_kusok(chisla, ncpu):
    zadachi = razbit_po_yadram(chisla, ncpu)
    if not zadachi:
        return []
    if len(zadachi) == 1:
        return sort_kuska(zadachi[0])
    pul = Pool(len(zadachi))
    gotovo =  pul.map(sort_kuska,  zadachi)

    pul.close()
    pul.join()
    return skeit_spiski(gotovo)


#делаются серии: читаем поток подряд, не больше pamyat чисел за раз
def sdelat_serii(flow, pamyat, ncpu, papka):
    serii = []
    nomer = 0
    while True:
        chisla = chitat_kusok(flow, pamyat)
        if not chisla:
            break
        otsort = obrabotat_kusok(chisla, ncpu)
        name = os.path.join(papka, 'seriya_' + str(nomer) + '.txt')
        zapisat_txt(name, otsort)
        serii.append(name)
        nomer += 1
    return serii

def merge_seriy(imena, dest):
    if len(imena)== 0:
        open(dest, 'w' ).close()
        return
    if len(imena) == 1:
        src = open(imena[0], 'r', encoding='utf-8')
        dst =open(dest, 'w', encoding='utf-8')
        dst.write(src.read())
        src.close()
        dst.close()
        return
    flowi = []
    kucha = []
    for i in range(len(imena)):
        f = open(imena[i], 'r', encoding='utf-8')
        flowi.append(f)
        stroka = f.readline()
        if stroka:
            heapq.heappush( kucha, (int(stroka.strip()), i))
    out = open(dest, 'w', encoding='utf-8')
    try:
        while kucha:
            val, i = heapq.heappop(kucha)
            out.write(str(val) + '\n')
            stroka = flowi[i].readline()
            if stroka:
                heapq.heappush(kucha, (int(stroka.strip()), i))
    finally:
        out.close()
        for f in flowi:
            f.close()

def neskolko_prohodov(serii, vyhod, max_k, papka):
    tekushie = list(serii)
    nomer = 0
    while len(tekushie) > 1:
        novye = []
        i = 0
        while i < len(tekushie):
            gruppa = tekushie[i:i + max_k]
            i += max_k
            if len(gruppa) == 1:
                novye.append(gruppa[0])
                continue
            nomer += 1
            dest = os.path.join(papka, 'slit_' + str(nomer) + '.txt')
            merge_seriy(gruppa, dest)
            novye.append(dest)
            for old in gruppa:
                if os.path.isfile(old):
                    os.remove(old)
        tekushie = novye
    if len(tekushie) == 0:
        open(vyhod, 'w').close()
    else:
        merge_seriy(tekushie, vyhod)
        if tekushie[0] != vyhod and os.path.isfile(tekushie[0]):
            os.remove(tekushie[0])


# имя выходного файла рядом со входом, без перезаписи
def name_vyhoda(vhod):
    papka = os.path.dirname(os.path.abspath(vhod))
    name = os.path.basename(vhod )
    baz, rassh = os.path.splitext(name)
    return os.path.join(papka, baz + '.sorted.txt')


# удаление временных файлов
#(туда записываем, чтобы разбирать на сортировку цифры по отдельности, тк вместе они не поместятся)
def pochistit(papka):
    if not os.path.isdir(papka):
        return
    for name in os.listdir(papka):
        p = os.path.join(papka, name)
        try:
            os.remove(p)
#на случай, если доступа к удалению временного файла не будет
        except   OSError:
            pass
    try:
        os.rmdir(papka)
    except OSError:
        pass


def main():
    if len(sys.argv) != 3:
        print('Usage:   python3 sort.py <filename> <mem_count>')
        sys.exit(1)

    vhod = sys.argv[1]
    try:
        pamyat = int(sys.argv[2])
    except ValueError:
        print('mem_count должен быть целым числом')
        sys.exit(1)

    if pamyat < 2:
        print('mem_count должен быть >= 2')
        sys.exit(1)

    if not os.path.isfile(vhod):
        print('нет такого файла')
        sys.exit(1)

    if not vhod.endswith('.txt'):
        print('нужен текстовый файл .txt')
        sys.exit(1)

    vyhod =  name_vyhoda(vhod)
    if os.path.abspath(vyhod) == os.path.abspath(vhod):
        print('нельзя перезаписывать входной файл')
        sys.exit(1)

    ncpu = cpu_count()
    if ncpu is None or ncpu < 1:
        ncpu = 1

    papka = os.path.join(os.path.dirname(os.path.abspath(vhod)),
                         '.tmp_sort_' + str(os.getpid()))
    os.mkdir(papka)

    flow = None
    try:
        flow = open(vhod, 'r', encoding='utf-8')
        serii = sdelat_serii(flow, pamyat, ncpu, papka)
        neskolko_prohodov(serii, vyhod,pamyat, papka)
    finally:
        if flow is not None:
            flow.close()
        pochistit(papka)


if __name__ == '__main__':
    main()
