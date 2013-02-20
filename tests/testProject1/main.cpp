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
  return function() + a + b;
}

TestClass::TestClass() {
}

TestClass::~TestClass() {
}

typedef TestClass TestTypeDef;

