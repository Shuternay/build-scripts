#include "testlib.h"

#include <set>

using namespace std;

int main() {
    registerValidation();

    int n = inf.readInt(1, 100000, "n");
    inf.readEoln();
    
    for (int i = 0; i < n; ++i) {
        inf.readInt(1, 1000000, format("a[%d]", i));
        if (i + 1 < n)
            inf.readSpace();
    }
    inf.readEoln();

    inf.readEof();

    return 0;
}
