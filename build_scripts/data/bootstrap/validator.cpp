#include "testlib.h"

#include <set>

using namespace std;

int main() {
    registerValidation();

    long T = inf.readLong(1, 100, "t");
    inf.readEoln();

    for (long t = 0; t < T; ++t) {
        inf.readLong(1, 30, format("t[%ld]: d", t));
        inf.readEoln();

        long n = inf.readLong(2, 100, format("t[%ld]: n", t));
        inf.readSpace();
        
        for (long i = 0; i < n; ++i) {
            inf.readLong(1, 100, format("t[%ld]: x[%ld]", t, i));
            if (i + 1 < n)
                inf.readSpace();
        }
        inf.readEoln();
    }

    inf.readEof();

    return 0;
}
