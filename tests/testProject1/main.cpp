class TestClass {
  public:
    TestClass();
    ~TestClass();
    int function(int a);
};

int TestClass::function(int a) {
  TestClass t; int b = a; a = b;
  TestClass* t2 = new TestClass();
  delete t2;
  return function(a + b);
}

TestClass::TestClass() {
}

TestClass::~TestClass() {
}

typedef TestClass TestTypeDef;

template<class T>
class TemplClassTest {
  public:
  TemplClassTest();
  ~TemplClassTest();
};

class TemplClassDerv : public TemplClassTest<int> {
};

template<class T>
TemplClassTest<T>::TemplClassTest() {
  TemplClassTest<double>* t = new TemplClassTest<double>();
}
template<class T>
TemplClassTest<T>::~TemplClassTest() {
}
