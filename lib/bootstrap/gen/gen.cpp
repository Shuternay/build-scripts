#include "testlib.h"
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <string>
#include <vector>
#include <set>

#if ( _WIN32 || __WIN32__ )
#define LLD "%I64d"
#else
#define LLD "%lld"
#endif

using namespace std;

int testNum = 0, tInf = 0;

enum OutputFormat {
    NORMAL, TESTLIB, SINGLE
};

void printTestInfo(const char *format, ...) {
    FILE *tf;
    if (tInf)
        tf = fopen("tests.info", "a");
    else
        tf = fopen("tests.info", "w"), tInf = 1;

    va_list marker;
    va_start(marker, format);
    fprintf(tf, "%03d: ", testNum + 1);
    vfprintf(tf, format, marker);
    fprintf(tf, "\n");
    va_end(marker);

    fclose(tf);
}

class TestCase {
public:

    TestCase() {
    }

    long n, m;
    vector<string> dict;
    string s;

    TestCase *process() {
        printTestInfo("shuffled string");

        return this;
    }

    void printTest(int outF) {
        testNum++;
        FILE *inf;

        switch (outF) {
            case NORMAL:
                char fileName[20];
                sprintf(fileName, "tests/%02d", testNum);
                inf = fopen(fileName, "w");
                break;
            case TESTLIB:
                startTest(testNum);
                inf = stdout;
                break;
            case SINGLE:
                inf = stdout;
                break;
        }

        fprintf(inf, "%ld\n", m);
        for (long i = 0; i < m; ++i)
            fprintf(inf, "%s\n", dict[i].c_str());
        fprintf(inf, "%s\n", s.c_str());

    }
};

TestCase genHandTest(int n) {
    TestCase t;



    return t;
}

TestCase genRandomTest(long n, long m = -1) {
    TestCase t;



    return t;
}

int main(int argc, char** argv) {

    registerGen(argc, argv, 1);

    int outF = argc > 1 ? atoi(argv[1]) : SINGLE;
    switch (outF) {
        case NORMAL:
        case TESTLIB:
            *genHandTest(0)->printTest(outF);
            *genHandTest(1)->printTest(outF);


            printTestInfo("group 1");
            *genRandomTest(1000)->process()->printTest(outF);


            printTestInfo("group 2");
            *genRandomTest(1000)->process()->printTest(outF);


            printTestInfo("group 3");
            *genRandomTest(1000)->process()->printTest(outF);

            break;

        case SINGLE:
            *genRandomTest(1000)->printTest(outF);
            break;
    }

    return 0;
}

