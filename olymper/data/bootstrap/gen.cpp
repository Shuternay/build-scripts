#include "testlib.h"
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>
#include <set>

#if ( _WIN32 || __WIN32__ )
#define LLD "%I64d"
#else
#define LLD "%lld"
#endif

using namespace std;

const char* testsPath = "tests";

int testNum = 0, tInf = 0;
int outF;
enum OutputFormat {
    NORMAL, TESTLIB, SINGLE
};

void printTestInfo(const char *format, ...) {
    if(outF == NORMAL) {
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
}

class TestCase {
public:
    vector<int> a;

    TestCase *addNoise(double p) {
        int cnt = 0;
        for(size_t i = 0; i < a.size(); ++i)
            if(rnd.next() < p) {
                a[i] = rnd.next(1, 1000000);
                cnt++;
            }

        printTestInfo("added noise, p = %lf, %d nums changed", p, cnt);
        return this;
    }

    TestCase *genHandTest(int tn) {
        if(tn == 0) {
            a = {4, 3, 4, 3};
        }
        else if(tn == 1) {
            a = {2, 4, 7, 5, 6};
        }

        printTestInfo("hand test, n = %d", (long)a.size());
        return this;
    }

    TestCase *genRandomTest(int n, bool randomness = false) {
        if(randomness)
            n = rnd.next(8 * n / 10, n);

        a.resize(n);
        for(int i = 0; i < n; ++i)
            a[i] = rnd.next(1, 1000000);

        printTestInfo("n = %d", n);

       return this;
    }

    TestCase *printTest() {
        testNum++;
        FILE *inf;

        switch (outF) {
            case NORMAL:
                char fileName[20];
                sprintf(fileName, "%s/%02d", testsPath, testNum);

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

        fprintf(inf, "%d\n", (int)a.size());
        for(size_t i = 0; i < a.size(); ++i) {
            fprintf(inf, "%d", a[i]);
            if(i + 1 < a.size())
                fprintf(inf, " ");
            else
                fprintf(inf, "\n");
        }

        if(outF == NORMAL)
            fclose(inf);

        if(outF == NORMAL)
            printf("%02d: generated\n", testNum);

        return this;
    }
};


int main(int argc, char** argv) {

    registerGen(argc, argv, 1);


    outF = argc > 1 ? atoi(argv[1]) : SINGLE;


    long long maxn = 2000; // problem maximum
    if(outF == SINGLE) {
        TestCase().genRandomTest(maxn)->printTest();
        return 0;
    }

    TestCase().genHandTest(0)->printTest();
    TestCase().genHandTest(1)->printTest();

    maxn = 100;
    printTestInfo("");
    printTestInfo("group 1, maxn = " LLD, maxn);
    TestCase().genRandomTest(maxn, true)->printTest();
    TestCase().genRandomTest(maxn, true)->printTest();

    return 0;
}

