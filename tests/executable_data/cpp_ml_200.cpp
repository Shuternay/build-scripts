#include <iostream>
#include <vector>

using namespace std;

int main(int argc, char** argv) {
    int mx = 50000000;

    vector<int> v(mx);
    for(int i = 1; i < mx; ++i)
       v[i] = v[i-1] ^ v[i / 10] ^ i;
    cout << v[0] + v.back() << "\n";
    return 0;
}
