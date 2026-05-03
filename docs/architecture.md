# System architecture
  
The architecture is divided into three main layers  

## 1. Preprocessing Layer  
- **Text cleaning:** Character normalization is performed, for example removing Spanish accents, etc.  
- **Segmentation:** The text is divided into sentences so the model does not lose context.  

## 2. Hybrid Inference Layer  
Two approaches are combined to detect entities  

1. **Pattern engine**  
   Handles structured entities, whose fixed formats can be detected with regex.  

2. **NER engine**  
   Handles unstructured entities that depend on context, such as names, surnames, addresses, or job titles. This component is critical because it detects entities based on context.  

## 3. Contextual Decision Layer  
In this layer, it is determined whether an entity is PII or not.  

## 4. Action and Transformation Layer  
Once the system marks sensitive data (tags the words), de-identification logic is applied:  
- **Masking:** Replacement with generic tags, for example `<PERSON>`, `<ID>`  
- **Pseudonymization:** Replacement with realistic fake names  