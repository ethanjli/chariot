dbclear all;
mex bfMex.cpp sms.cpp CXXFLAGS="\$CXXFLAGS -std=c++0x -fpermissive"
mex smsMex.cpp sms.cpp CXXFLAGS="\$CXXFLAGS -std=c++0x -fpermissive"
disp('Done Sms!');
