clc
close all
clear

%--------------------------------------
disp('Estimulacion');

n = 1; %% seria la funcion micros

b_var = [1, 0, 0, 0];

% ts, pw, pwr, val min mA, val max mA, time values
%  1,  2,   3,          4,          5,
%ul_var = [1000, 1, 1, 1, 10, 6e6, 1e6, 1e5];
ul_var = [12000, 5, 195, 1, 10, 6e6, 1e6, 1e5];

x = zeros(ul_var(1));
c = 1;

% act ch1, paso mA, ton/ts, toff, ri, rf
%       1,       2,      3,    4,  5,  6
data_sps = [1, 3.76, 2000, 5000, 1000, 2000; 0, 0, 0, 0, 0, 0];

seq = 1;                            % secuencia de la senal general  canal 1
spw = 1;                            % secuencia de la señal especifica canal 1
mA = 0;                             % varible para contar pasos mA en ri y rf

% valores iniciales de tiempo para la señal
ul_vt = [0, 0, 0];

ul_vt(1) = n + ul_var(1);               % valor final de tiempo

% valor inicial rampa o tsus
%disp('Ton >>>>>>>');
if data_sps(1,5) > 0
    ul_vt(2) = n + data_sps(1,5);       % tiempo de ramap
    seq = 1;
    %disp('Ramp Up');
    mA = data_sps(1, 2);
    disp(mA);
    x(c) = mA;
    c = c+1;
else
    ul_vt(2) = n + data_sps(1,3);       % tiempo de sustentacion
    seq = 2;
    %disp('Support');
    mA = ul_var(5);
    disp(mA);
    x(c) = mA;
    c = c+1;
end

ul_vt(3) = n + ul_var(2);               % tiempo pwm inicial



%disp(paso_ma1); % aqui comienza a generar la señal

while n < ul_vt(1)
    if data_sps(1,1) == 1
        if n >= ul_vt(2)
            disp(0);
            x(c) = 0;
            c = c+1;
            switch seq
                case 1 % rampa up
                    seq = 2;
                    ul_vt(2) = n + data_sps(1,3);
                    %disp('Support');
                case 2 % sustentacion
                    if data_sps(1,6) > 0
                        seq = 3;
                        ul_vt(2) = n + data_sps(1,6);
                        %disp('Ramp Down');
                    else
                        seq = 4;
                        ul_vt(2) = n + data_sps(1,4);
                        %disp('Toff');
                        mA = 0;
                    end
                case 3 % ramapa down
                    seq = 4;
                    ul_vt(2) = n + data_sps(1,4);
                    %disp('Toff');
                    mA = 0;
                case 4 % t off
                    if data_sps(1,5) > 0
                        seq = 1;
                        ul_vt(2) = n + data_sps(1,5);
                        %disp('Ramp Up');
                    else
                        seq = 2;
                        ul_vt(2) = n + data_sps(1,3);
                        %disp('Support');
                    end
            end
        end
        
        %-------------------------------------------------------------%
        %------------------ Make signal ------------------------------%
        %-------------------------------------------------------------%
        if n >= ul_vt(3) && seq < 4
            switch spw
                case 1 % mA +
                    spw = 2;
                    ul_vt(3) = n + ul_var(2);
                    disp(-mA);
                    x(c) = -mA;
                    c = c+1;
                case 2 % mA -
                    spw = 3;
                    ul_vt(3) = n + ul_var(3);
                    disp('0');
                    x(c) = 0;
                    c = c+1;
                    switch seq
                        case 1 % mA +
                            if mA < ul_var(5)
                                mA = mA + data_sps(1,2);
                            end
                        case 2 % mA -
                            mA = ul_var(5);
                        case 3 % ramapa down
                            if mA > 0
                                mA = mA - data_sps(1,2);
                            end
                    end
                case 3 % ramapa down
                    spw = 1;
                    ul_vt(3) = n + ul_var(2);
                    disp(mA);
                    x(c) = mA;
                    c = c+1;
            end
        end
    end
    n = n + 1;
end

plot(x);