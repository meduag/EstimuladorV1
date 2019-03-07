clc
close all
clear

%--------------------------------------
disp('Estimulacion');

t_min = 6000000;
t_seg = 1000000;
t_mil = 100000;

n = 1; %% seria la funcion micros

b_var = [1, 0, 0, 0];

ul_var = [0, 0, 0, 0, 0, t_min, t_seg, t_mil];

data_sps = [0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0];

% valores iniciales de teste
ul_var(1) = 1000;               % ts
ul_var(2) = 2;                  % pw
ul_var(3) = 2;                  % pwr
ul_var(4) = 10;                 % valor maximo de corriente

b_var(1) = 0;                   % tex = 0

data_sps(1,1) = 1;           % ch1 activado

% valor paso de miliamps data_sp[0].sps[1]
% data_sps(1,2) >>> pasa el valor de paso de miliamps
paso_ma1 = 0.9;                % valor de paso para los miliamps
data_sps(1,3) = 40;          % ton
data_sps(1,4) = 100;         % tof
data_sps(1,5) = 30;          % ri
data_sps(1,6) = 30;          % rf

data_sps(2,1) = 0;           % Ch2 desactivado

sec = 1;                        % secuencia de la senal general  canal 1
sect = 0;
sec_pw = 1;                     % secuencia de la señal especifica canal 1
mA = 0;                         % varible para contar pasos mA en ri y rf

% valores iniciales de tiempo para la señal
ul_vt = [0, 0, 0];
ul_vt(1) = n + ul_var(1);
ul_vt(2) = n + data_sps(1,5);
ul_vt(3) = n + ul_var(2);

%disp('Ton >>>>>>>');
%disp('Ramp Up');
%disp(paso_ma1); % aqui comienza a generar la señal

x = zeros(500);
c = 1;

while n < ul_vt(1)
    % example
    % 60>500>19000>1>20>1>1500>2>2>5>5>1>1500>2>2>5>5>0>1>0>
    if data_sps(1,1) == 1
        if sec ~= 0
            switch sec
                case 10
                    if n >= ul_vt(2)
                        sec = sect;
                    end
                case 1
                    if mA <= (ul_var(4) - paso_ma1)
                        mA = mA + paso_ma1;
                        sect = sec;
                        disp(mA);
                        x(c) = mA;
                        c = c+1;
                        sec = 10;
                    end
                    if n >= ul_vt(2) % si es mayor que el valor de rampa up pasa a suport
                        %disp('Support');
                        sec = 2;
                        mA = ul_var(4);
                        switch sec_pw
                            case 1 % esta + pasa a -
                                sec_pw = 2;
                                disp(mA);
                                x(c) = mA;
                                c = c+1;
                            case 2 % esta - pasa a 0
                                sec_pw = 3;
                                disp('0');
                                x(c) = 0;
                                c = c+1;
                            case 3 % esta no 0´pasa +
                                sec_pw = 2;
                                disp(-mA);
                                x(c) = -mA;
                                c = c+1;
                        end
                        ul_vt(2) = n + data_sps(1,3);
                        sect = sec;
                    end
                case 2
                    if n >= ul_vt(2)
                        if b_var(3) == 0
                            %disp('Ramp down');
                            sec = 3;
                            sect = sec;
                            if mA >= 0
                                mA = mA - paso_ma1;
                            end
                            switch sec_pw
                                case 1 % esta + pasa a -
                                    sec_pw = 1;
                                    disp(mA);
                                    x(c) = mA;
                                    c = c+1;
                                case 2 % esta - pasa a 0
                                    sec_pw = 3;
                                    disp('0');
                                    x(c) = 0;
                                    c = c+1;
                                case 3 % esta no 0´pasa +
                                    sec_pw = 2;
                                    disp(-mA);
                                    x(c) = -mA;
                                    c = c+1;
                            end
                            ul_vt(2) = n + data_sps(1,6);
                            ul_vt(3) = n + ul_var(2);
                        else
                            %disp('Toff >>>>>>>');
                            sec = 0;
                            sec_pw = 1;
                            ul_vt(2) = n + data_sps(1,4);
                            disp('0');
                            x(c) = 0;
                            c = c+1;
                        end
                    else
                        disp(mA);
                        x(c) = mA;
                        c = c+1;
                    end
                    sec = 10;
                    
                case 3
                    if mA >= 0
                        mA = mA - paso_ma1;
                        sect = sec;
                        disp(mA);
                        x(c) = mA;
                        c = c+1;
                        sec = 10;
                    end
                    
                    if n >= ul_vt(2) % si es mayor que el valor de rampa up pasa a suport
                        %disp('Toff >>>>>>>');
                        sec = 0;
                        sec_pw = 0;
                        ul_vt(2) = n + data_sps(1,4);
                        disp('0');
                        x(c) = 0;
                        c = c+1;
                    end
            end
            
            %-------------------------------------------------------------
            %------------------ Make signal ------------------------------
            %-------------------------------------------------------------
            switch sec_pw
                case 1
                    if n >= ul_vt(3)
                        disp(-mA);
                        x(c) = -mA;
                        c = c+1;
                        ul_vt(3) = n + ul_var(2);
                        sec_pw = 2;
                        
                    else
                        sec = 10;
                    end
                case 2
                    if n >= ul_vt(3)
                        disp("0");
                        x(c) = 0;
                        c = c+1;
                        ul_vt(3) = n + ul_var(3);
                        sec_pw = 3;
                    end
                case 3
                    if n >= ul_vt(3)
                        sec_pw = 1;
                        sec = sect;
                        ul_vt(3) = n + ul_var(2);
                    end
            end
            %-------------------------------------------------------------
            %------------------ Make signal ------------------------------
            %-------------------------------------------------------------
        end
        
        if sec == 0 && n >= ul_vt(2)
            %disp('Ton >>>>>>>');
            %disp('Ramp Up');
            ul_vt(2) = n + data_sps(1,5);
            sec = 1;
            sec_pw = 1;
            mA = 0;
        end
    end
    
    n = n + 1;
    if n == 75
        %disp('Debug');
    end
    %disp('valor de n:');
    %disp(n);
end

plot(x);
%disp('Terminou');




