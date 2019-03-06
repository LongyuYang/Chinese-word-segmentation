
#_*_coding:utf-8_*_
import pycrfsuite
import wx

#**************************************************************************
#         为语料库的字标注 S,B,E,M
#**************************************************************************
def encode(open_file, store_file):
    f = open(open_file, 'r')
    s = []  #词表
    for line in f:
        s.extend(line.split())
    f.close()
    f = open(store_file, 'w')
    length = len(s)
    for i in range(length):
        str = s[i]
        if str[0] >= '0' and str[0] <= '9': #数字
            str = str[:-2]
            f.write(str + '/S\n')
            continue
        if str[0] == '[':
            str = str[1:]
        if str[-2] == '/':
            str = str[:-2]
        elif str[-3] == '/':
            str = str[:-3]
        elif str[-5] == '/':
            str = str[:-5]
        length = len(str)
        if length == 2:
            f.write(str[0] + str[1] + '/S\n')
        else:
            f.write(str[0] + str[1] + '/B\n')
            i = 2
            while i < length - 3:
                f.write(str[i] + str[i+1] + '/M\n')
                i = i + 2
            f.write(str[i] + str[i+1] + '/E\n')
    f.close()


#**************************************************************************
#                          建立特征
#**************************************************************************
def build_features(s, start, end):
    features_list = []
    i = start
    while i < end:
        features = {}
        if i == 0:
            features['c-2'] = '_'
            features['c-1'] = '_'
            features['c-2-1'] = '__'
            features['c-10'] = '_' + s[i]
        elif i == 1:
            features['c-1'] = s[i-1]
            features['c-2'] = '_'
            features['c-2-1'] = '_' + s[i-1]
            features['c-10'] = s[i-1] + s[i]
        else:
            features['c-1'] = s[i-1]
            features['c-2'] = s[i-2]
            features['c-2-1'] = s[i-2] + s[i-1]
            features['c-10'] = s[i-1] + s[i]
        if i == end - 1:
            features['c2'] = '_'
            features['c1'] = '_'
            features['c01'] = s[i] + '_'
        elif i == end - 2:
            features['c2'] = '_'
            features['c1'] = s[i+1]
            features['c01'] = s[i] + s[i+1]
        else:
            features['c2'] = s[i+2]
            features['c1'] = s[i+1]
            features['c01'] = s[i] + s[i+1]
        if i == 0:
            features['c-11'] = '_' + s[i] + s[i+1]
        elif i == end - 1:
            features['c-11'] = s[i-1] + s[i] + '_'
        else:
            features['c-11'] = s[i-1] + s[i] + s[i+1]
        features_list.append(features)
        i = i + 1
    return features_list


#**************************************************************************
#         建立训练数据的特征
#**************************************************************************
def train_features(filename):
    f = open(filename)
    s = []
    l = []
    for line in f:
        str = line.strip()
        s.append(str[:-2])
        l.append(str[-1])
    length = (int)(len(s))
    feature_list1 = build_features(s, 0, length/2)
    labels1 = l[:length/2]
    feature_list2 = build_features(s, length/2, length)
    labels2 = l[length/2:]
    return feature_list1, feature_list2, labels1, labels2


#**************************************************************************
#         建立测试数据特征
#**************************************************************************
def test_features(filename):
    f = open(filename)
    s = []
    str = f.read().strip()
    i = 0
    length = len(str)
    while i < length - 1:
        if str[i] >= '0' and str[i] <= '9':
            j = i
            tmp = ''
            while str[j] >= '0' and str[j] <= '9' and j < length - 1: #数字
                tmp = tmp + str[j]
                j = j + 1
            i = j
            s.append(tmp)
            continue
        if ord(str[i]) < 127:
            s.append(str[i])
            i = i + 1
            continue
        s.append(str[i] + str[i+1])
        i = i + 2
    length = len(s)
    features_list = build_features(s, 0, length)
    return features_list, s


#**************************************************************************
#         将标记S,B,M,E的测试语料转换为最终分词结果
#**************************************************************************
def decode(filename, s, tag):
    f = open(filename, 'w')
    length = len(s)
    line_counter = 0
    i = 0
    result_str = ''
    while i < length:
        if tag[i] == 'S':
            f.write(s[i] + ' ')
            result_str += s[i] + '  '
            i = i + 1
        else:
            j = i
            while tag[j] != 'E':
                f.write(s[j])
                result_str += s[j]
                j = j + 1
                if (j >= length):
                    break
            if (j < length):
                f.write(s[j] + ' ')
                result_str += s[j] + '  '
            i = j + 1
        line_counter = line_counter + 1
        if line_counter == 12:
            line_counter = 0
            f.write('\n')
    f.close()
    return result_str


#**************************************************************************
#                 建立窗口显示结果
#**************************************************************************
class mywin(wx.Frame):
    def __init__(self, parent, title):
        super(mywin, self).__init__(parent, title = title)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        stcText = wx.StaticText(panel, id = -1, label = 'Result',  style = wx.ALIGN_CENTER)
        self.text = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
        vbox.Add(stcText, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(self.text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        font = wx.Font(16, wx.ROMAN, wx.NORMAL, wx.NORMAL)
        self.text.SetFont(font)
        panel.SetSizer(vbox)
        self.SetSize((400, 300))
        self.Center()
        self.Show()
        self.Fit()


#**************************************************************************
#         主函数   the model is pre-trained
#**************************************************************************
'''
encode('199801.txt', 'tmp.txt')
feature_list1, feature_list2, label1, label2 = train_features('tmp.txt')
trainer = pycrfsuite.Trainer()
trainer.append(feature_list1,label1)
trainer.append(feature_list2,label2)
trainer.train('model')
'''

tagger = pycrfsuite.Tagger()
tagger.open('model')
test_list, s = test_features('test.txt')
tag = tagger.tag(test_list)
app = wx.App()
x = mywin(None, 'segment')
result_str = decode('result.txt', s, tag)
x.text.write(unicode(result_str, 'mbcs'))

app.MainLoop()

#build exe:
#nuitka --recurse-all test.py --recurse-directory=D:\python_project\first\venv\Lib\site-packages\pycrfsuite --standalone



