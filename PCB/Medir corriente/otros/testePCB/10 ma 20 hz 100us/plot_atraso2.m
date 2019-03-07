%% Initialize variables.
% filename = 'C:\Users\medua\Dropbox\00Iniciode_Doctorado\008 semestre final\EstimulemaPCB\Medir corriente\testePCB\10 ma 20 hz 100us\T0000.CSV';
% filename = 'C:\Users\medua\Dropbox\00Iniciode_Doctorado\008 semestre final\EstimulemaPCB\Medir corriente\testePCB\sinal filtrado con carga desconectada\T0000.CSV';
filename = 'C:\teste r\T0009.CSV';
delimiter = ',';
startRow = 16;

%% Format for each line of text:
formatSpec = '%f%f%f%f%f%[^\n\r]';

%% Open the text file.
fileID = fopen(filename,'r');

%% Read columns of data according to the format.
textscan(fileID, '%[^\n\r]', startRow-1, 'WhiteSpace', '', 'ReturnOnError', false, 'EndOfLine', '\r\n');
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter, 'TextType', 'string', 'EmptyValue', NaN, 'ReturnOnError', false);

%% Close the text file.
fclose(fileID);

%% Create output variable
T0000 = table(dataArray{1:end-1}, 'VariableNames', {'TIME','CH1','CH1PeakDetect','CH2','CH2PeakDetect'});

%% Clear temporary variables
clearvars filename delimiter startRow formatSpec fileID dataArray ans;

%% Split data
ch1 = T0000(:,2);
ch2 = T0000(:,4);
chv1 = ch1.CH1;
chv2 = ch2.CH2;

figure()
plot(chv1);
hold on
plot(chv2);
%plot(ch3)

ordenf = 6;
fc = 20;
fs = 125000/2;
rp = 0.2;

lpFilt2 = designfilt('lowpassiir','FilterOrder',ordenf, ...
         'PassbandFrequency',fc,'PassbandRipple',rp, ...
         'SampleRate',fs);
     
chf1 = filter(lpFilt2,chv1);
chf2 = filter(lpFilt2,chv2);

figure();
plot(chf1,'r');
hold on
plot(chf2,'b');

sus = chf1 - chf2;
plot(sus);

