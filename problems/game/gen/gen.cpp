#include "testlib.h"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <set>

#if ( _WIN32 || __WIN32__ )
#define LLD "%I64d"
#else
#define LLD "%lld"
#endif

using namespace std;

int testNum = 0;

enum OutputFormat {
    NORMAL, TESTLIB, SINGLE
};

class TestCase {
public:

    TestCase() {
    }

    void setDim(long n) {
        x.resize(n);
    }

    long d;
    vector<long> x;
};

void printTest(vector<TestCase> &t, int outF) {
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

    fprintf(inf, "%u\n", t.size());

    for (size_t i = 0; i < t.size(); ++i) {
        fprintf(inf, "%ld\n", t[i].d);

        fprintf(inf, "%u ", t[i].x.size());
        for (size_t j = 0; j < t[i].x.size(); ++j) {
            fprintf(inf, "%ld", t[i].x[j]);
            if (j + 1 < t[i].x.size())
                fprintf(inf, " ");
        }
        fprintf(inf, "\n");
    }
}

vector<TestCase> &genSampleTest(vector<TestCase> &t) {
    t.resize(3);

    t[0].d = 1;
    t[0].setDim(2);
    t[0].x[0] = 5;
    t[0].x[1] = 3;

    t[1].d = 3;
    t[1].setDim(4);
    t[1].x[0] = 3;
    t[1].x[1] = 3;
    t[1].x[2] = 4;
    t[1].x[3] = 3;

    t[2].d = 7;
    t[2].setDim(3);
    t[2].x[0] = 7;
    t[2].x[1] = 6;
    t[2].x[2] = 7;

    return t;
}

vector<TestCase> &genRandomTest(vector<TestCase> &t, long tN, long maxDim, bool randomness) {
    t.resize(tN);
    
    int flag = 0;
    if(rnd.next() < 0.2)
       flag = 1;

    for (long i = 0; i < tN; ++i) {
        t[i].d = rnd.next(1, flag ? 5 : 30);
        if (randomness)
            t[i].setDim(rnd.next(max(7 * maxDim / 10, 2l), maxDim));
        else
            t[i].setDim(maxDim);

        for (long j = 0; j < t[i].x.size(); ++j) {
	    if(!flag) {
	        if(rnd.next() < 0.3 / t[i].x.size() || i == 3)
                    t[i].x[j] = rnd.next(1l, max(t[i].d - 1, 1l));
	        else
                    t[i].x[j] = rnd.next(t[i].d, 100l);
            }
	    else
	        t[i].x[j] = (2 * rnd.next(0, 9) + 1) * t[i].d + rnd.next(0l, t[i].d-1);
	}
    }
    
    return t;
}

int main(int argc, char** argv) {

    registerGen(argc, argv, 1);

    int outF = atoi(argv[1]);

    vector<TestCase> t;
    
    switch (outF) {
        case NORMAL:
        case TESTLIB:

            printTest(genSampleTest(t), outF);

            for (long i = 0; i < 6; ++i) // 2 - 7
                printTest(genRandomTest(t, 5, 4, true), outF);
            
            for (long i = 0; i < 6; ++i) // 8 - 13
                printTest(genRandomTest(t, 100, 4, true), outF);
            
            for (long i = 0; i < 8; ++i) // 14 - 21
                printTest(genRandomTest(t, 100, 100, true), outF);
            break;

        case SINGLE:
            printTest(genRandomTest(t, 100, 100, true), outF);
            break;
    }

    return 0;
}

