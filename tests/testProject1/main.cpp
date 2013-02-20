class TestClass {
  public:
    TestClass();
    ~TestClass();
    int function();
};

int TestClass::function() {
  TestClass t;
  TestClass* t2 = new TestClass();
  delete t2;
  return function();
}

TestClass::TestClass() {
}

TestClass::~TestClass() {
}

typedef TestClass TestTypeDef;

