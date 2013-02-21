
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
