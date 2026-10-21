package com.baseball.commons.config;


import java.io.IOException;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

/**
 * Feign 配置 - 支持文件上传
 */
// @Configuration
// public class FeignConfig {
//
//     public class MultipartSupportConfig implements feign.codec.Encoder {
//         private final feign.codec.Encoder delegate;
//
//         public MultipartSupportConfig(feign.codec.Encoder delegate) {
//             this.delegate = delegate;
//         }
//
//         @Override
//         public void encode(Object object, Type type, RequestTemplate template) throws EncodeException {
//             if (object instanceof Map) {
//                 Map<String, Object> data = (Map<String, Object>) object;
//                 Map<String, Object> formData = new HashMap<>();
//
//                 for (Map.Entry<String, Object> entry : data.entrySet()) {
//                     if (entry.getValue() instanceof byte[]) {
//                         // 字节数组处理
//                         formData.put(entry.getKey(), entry.getValue());
//                     } else {
//                         formData.put(entry.getKey(), entry.getValue());
//                     }
//                 }
//                 template.body(formData);
//             } else {
//                 delegate.encode(object, type, template);
//             }
//         }
//     }
// }