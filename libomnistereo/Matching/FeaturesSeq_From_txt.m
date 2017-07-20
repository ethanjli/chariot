function FeaturesSeq_From_txt ( file_name, cor_name, begin_seq)

if nargin == 1
    %% Load Correspondence Points KorresFirst and KorresSecond
    NumPoints = load( sprintf( '%s/Corners/KorresNums_LR.txt', file_name));
    Korres = load( sprintf( '%s/Corners/KorresPoints_LR.txt', file_name));

    begin = 1;

    for seq=1:size(NumPoints,1)% 80:120%:size(NumPoints)

        fprintf(1,'Run calculation for %d\n',seq);

         if seq == begin
             KorresFir= Korres(1:NumPoints(seq),1:4);
             KorresSec = Korres(1:NumPoints(seq),5:8);
             KorresLength = size(KorresFir,1);
         else
             KorresFir = Korres(KorresLength+1:KorresLength+NumPoints(seq),1:4);
             KorresSec = Korres(KorresLength+1:KorresLength+NumPoints(seq),5:8);
             KorresLength = KorresLength + size(KorresFir,1);
         end

        corners{1,1}.p = KorresFir(:,1:2);
        corners{1,2}.p = KorresFir(:,3:4);
        corners{1,3}.p = KorresSec(:,1:2);
        corners{1,4}.p = KorresSec(:,3:4);

        save(sprintf('%s/Corners/corners_%06d.mat',file_name, seq), 'corners');
    end
    
else
    
    for seq = begin_seq %: end_seq
       
       % filename = sprintf( '%s/KorresPoints_LR_%010d_%010d.txt', cor_name, seq-1, seq);
        filename = sprintf( '%s/KorresPoints_LR_%010d_%010d.txt', cor_name, seq, seq+1 );
        if exist( filename) == 2
            Korres = load ( filename );
        else
            error('ERROR: Correspondences does not exist. \n');
        end
       
       corners{1,1}.p = Korres(:,1:2);
       corners{1,2}.p = Korres(:,3:4);
       corners{1,3}.p = Korres(:,5:6);
       corners{1,4}.p = Korres(:,7:8);
       
       save(sprintf('%scorners_%06d.mat',file_name, seq), 'corners');
    
    end
    
end